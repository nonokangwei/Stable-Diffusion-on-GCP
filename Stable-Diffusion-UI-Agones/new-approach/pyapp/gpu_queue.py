
import sys
from wsgiref import simple_server

import combine_alloc
import falcon


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


class ShallWait:
  def on_post(self, req, resp):
    input_data = req.media
    task = ""
    userid = req.get_header("X-Sdui-User-Id")
    if input_data["data"]:
      ttask = input_data["data"][0]
      if ttask[0:4] == "task":
        task = ttask
    if check_wait(task, userid) == 0:
      resp.media = {"wait": True}
    else:
      resp.media = {"wait": False}
    resp.status = 200


class Progress:
  """The Progress class."""

  def on_post(self, req, resp):
    """Get the progress."""
    input_data = req.media
    id_task = input_data["id_task"]
    userid = req.get_header("X-Sdui-User-Id")
    if check_wait(id_task, userid) == 0:
      r = {"active": False,
           "queued": True,
           "completed": False,
           "progress": None,
           "eta": None,
           "live_preview": None,
           "id_live_preview": -1,
           "textinfo": "Waiting GPU..."}
    elif check_wait(id_task, userid) == 1:
      r = {"active": True,
           "queued": True,
           "completed": False,
           "progress": None,
           "eta": None,
           "live_preview": None,
           "id_live_preview": -1,
           "textinfo": "Waiting GPU..."}
      update_wait(id_task, userid)
    else:
      r = {"active": True,
           "queued": False,
           "completed": False,
           "progress": None,
           "eta": None,
           "live_preview": None,
           "id_live_preview": -1,
           "textinfo": "Waiting GPU..."}
    resp.media = r
    resp.status = 200


app = falcon.App()

# API to generate terraform script
app.add_route("/thehidden/shallwait", ShallWait())
app.add_route("/thehidden/queue", Progress())
app.add_route("/internal/progress", Progress())

if __name__ == "__main__":
  port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
  with simple_server.make_server("", port, app) as httpd:
    print(f"Serving on port {port}...")
    httpd.serve_forever()
