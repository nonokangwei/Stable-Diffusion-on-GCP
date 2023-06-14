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

def calc_userid(req):
  acct = req.get_header("x-goog-authenticated-user-email",
                        default="accounts.google.com:me@somewhere.com")
  _, email = acct.split(":")
  user, _ = email.split("@")
  hmac = hashlib.md5(b"ccccbeef" + acct.encode("utf8")).hexdigest()
  return f"{user}-{hmac}"


class Alloc:

  def on_post(self, req, resp):
    input_data = req.media
    task = "dummy"
    if input_data["data"]:
      userid = input_data["data"]["userid"]
      check_wait(task, userid)
      resp.media = {"processed": True}
      resp.status = 201
      return
    resp.status = 409
    res.media = {"reason":"invalid request"}

app = falcon.App()
app.add_route("/creategs", Alloc())

if __name__ == "__main__":
  port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
  with simple_server.make_server("", port, app) as httpd:
    print(f"Serving on port {port}...")
    httpd.serve_forever()
