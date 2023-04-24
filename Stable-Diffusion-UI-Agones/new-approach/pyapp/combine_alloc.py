#!/usr/bin/env python3
import json
import subprocess
import sys
import requests

SERVICE_TMPL = """apiVersion: v1
kind: Service
metadata:
  name: {userid}
  namespace: default
spec:
  selector:
    agones.dev/gameserver: {gs}
    agones.dev/role: gameserver
  ports:
    - protocol: TCP
      port: 80
      targetPort: 7860
"""
GSA_TMPL = """apiVersion: "allocation.agones.dev/v1"
kind: GameServerAllocation
metadata:
  name: {userid}-append
  namespace: default
spec:
  metadata:
    labels:
      sdui/userid: {userid}
"""


def kubectl(inp, *args):
  inp_byt = inp.encode("utf-8") if inp else None
  try:
    sub = subprocess.run(["kubectl", "-o", "json", *args],
                         input=inp_byt, capture_output=True, check=True)
  except subprocess.CalledProcessError as e:
    raise Exception(f"""{str(e)},\nstderr:\n{e.stderr}\n""") from e
  return sub.stdout.decode("utf-8")


def check_svc(userid, gs):
  svc = SERVICE_TMPL

  if not gs:
    return None, None

  try:
    s_res = json.loads(kubectl(None, "get", "svc", userid))
    if s_res["spec"]["selector"]["agones.dev/gameserver"] == gs:
      annt = s_res["metadata"]["annotations"].get("sdui/active")
      return userid, annt
  except Exception as e:
    print("check_svc", e, file=sys.stderr)
    pass

  try:
    kubectl(svc.format(userid=userid, gs=gs),
            "apply", "-f", "-")
  except subprocess.CalledProcessError as e:
    print(e, e.stderr, sys.stderr)

  kubectl(None, "annotate", "svc", userid, "sdui/active-")

  return userid, None


def check_svc_health(userid, annt):
  if userid is None:
    return userid, annt
  try:
    request = requests.request("GET", f"http://{userid}.default.svc.cluster.local/")
    if request.status_code == 200:
      return userid, annt
  except Exception as e:
    print("check_svc_health", e, file=sys.stderr)
  return None, None


def annotate(userid):
  kubectl(None, "annotate", "svc", userid, "sdui/active=2")


def check_gs(userid):
  res = kubectl(None, "get", "gs", "-l", f"sdui/userid={userid}")
  gss = json.loads(res)["items"]
  if gss:
    gs = gss[0]["metadata"]["name"]
    return gs
  return None


def create_gsa(userid):
  gsa = GSA_TMPL
  res = kubectl(gsa.format(userid=userid), "create", "-f", "-")
  gsa_res = json.loads(res)
  if "ports" not in gsa_res["status"]:
    return None
  gs = gsa_res["status"]["gameServerName"]
  return gs


def combine_alloc(userid):
  res = check_svc_health(*check_svc(userid, check_gs(userid)))
  if res[0]:
    return res
  res = check_svc_health(*check_svc(userid, create_gsa(userid)))
  if res[0]:
    return res
  return None, None


def main():
  userid = sys.argv[1]
  if combine_alloc(userid)[0]:
    sys.exit(0)
  else:
    sys.exit(1)


if __name__ == "__main__":
  main()
