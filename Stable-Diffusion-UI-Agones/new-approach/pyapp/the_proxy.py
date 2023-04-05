
import io
import json
import falcon
import hashlib
import os
import requests
import sys
from wsgiref import simple_server

import combine_alloc


fall_back = os.getenv("FALLBACK", "http://127.0.0.1:7860")
dft_namespace = os.getenv("DFT_NS", "default")


def check_wait(task, userid):
  if not task:
    return 2
  res, anno = combine_alloc.combine_alloc(userid)
  if res:
    if anno:
      return 2
    return 1
  return 0


def update_wait(task, userid):
  if not task:
    return
  combine_alloc.annotate(userid)


class Proxy(object):

  def __init__(self):
    self.session = requests.Session()

  def handle(self, req, resp):
    data = req.bounded_stream.read()

    headers = req.headers
    if "CONTENT-LENGTH" in headers and not headers["CONTENT-LENGTH"]:
      headers.pop("CONTENT-LENGTH")

    request = requests.Request(req.method, fall_back + req.relative_uri,
                               data=data,
                               headers=headers)
    prepared = request.prepare()
    from_upstream = self.session.send(prepared, stream=True)

    resp.content_type = from_upstream.headers.get("Content-Type",
                                                  falcon.MEDIA_HTML)

    resp.status = falcon.code_to_http_status(from_upstream.status_code)
    if from_upstream.status_code != 200:
      print("Proxy", from_upstream.status_code, req.method, req.relative_uri, file=sys.stderr)
    resp.stream = from_upstream.iter_content(io.DEFAULT_BUFFER_SIZE)


def handle_single(backend, req, resp):
  headers = req.headers
  if "CONTENT-LENGTH" in headers and not headers["CONTENT-LENGTH"]:
    headers.pop("CONTENT-LENGTH")
  data = json.dumps(req.media)
  request = requests.request(req.method, backend + req.relative_uri,
                             data=data,
                             headers=headers)
  resp.status = falcon.code_to_http_status(request.status_code)
  resp.media = request.json()


prxy = Proxy()


def calc_userid(req):
  acct = req.get_header("x-goog-authenticated-user-email",
                        default="accounts.google.com:me@somewhere.com")
  _, email = acct.split(":")
  user, _ = email.split("@")
  hmac = hashlib.md5(b"ccccbeef" + acct.encode("utf8")).hexdigest()
  return f"{user}-{hmac}"


class Predict:

  def on_post(self, req, resp):
    input_data = req.media
    userid = calc_userid(req)
    task = ""
    backend = f"http://{userid}.{dft_namespace}.svc.cluster.local"
    if input_data["data"]:
      ttask = input_data["data"][0]
      if ttask[0:4] == "task":
        task = ttask
    if not task:
      handle_single(fall_back, req, resp)
      return
    for cnt in range(3600):
      if cnt%60 == 0:
        print(f"waiting {cnt}", file=sys.stderr)
      if check_wait(task, userid) == 0:
        continue
      else:
        handle_single(backend, req, resp)
        return



class Progress:
  """The Progress class."""

  def on_post(self, req, resp):
    """Get the progress."""
    input_data = req.media
    id_task = input_data["id_task"]
    userid = calc_userid(req)
    backend = f"http://{userid}.{dft_namespace}.svc.cluster.local"
    r = {"active": False,
         "queued": False,
         "completed": False,
         "progress": None,
         "eta": None,
         "live_preview": None,
         "id_live_preview": -1,
         "textinfo": "Waiting GPU..."}
    match check_wait(id_task, userid):
      case 0:
        r["queued"] = True
        resp.media = r
        resp.status = 200
        return

      case 1:
        handle_single(backend, req, resp)
        if resp.media["active"]:
          return
        update_wait(id_task, userid)
        r["active"] = True
        r["queued"] = True
        r["textinfo"] = "Waiting GPU..."
        resp.status = 200
        resp.media = r
        return
      case x:
        print("progress", x, file=sys.stderr)
        handle_single(backend, req, resp)
        return

    resp.media = r
    resp.status = 200


app = falcon.App()
app.add_route("/internal/progress", Progress())
app.add_route("/run/predict/", Predict())
app.add_sink(prxy.handle, "/")

if __name__ == "__main__":
  port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
  with simple_server.make_server("", port, app) as httpd:
    print(f"Serving on port {port}...")
    httpd.serve_forever()
