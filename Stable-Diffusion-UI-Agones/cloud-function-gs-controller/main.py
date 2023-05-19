from flask import escape
from kubernetes import client, config
# from google.auth import compute_engine
# from google.cloud.container_v1 import ClusterManagerClient
from os import path
import requests
import yaml
import socket
import time
import base64
import json
import os

def get_access_token():
    METADATA_URL = 'http://metadata.google.internal/computeMetadata/v1/'
    METADATA_HEADERS = {'Metadata-Flavor': 'Google'}
    SERVICE_ACCOUNT = 'default'

    url = '{}instance/service-accounts/{}/token?scopes=https://www.googleapis.com/auth/cloud-platform'.format(METADATA_URL, SERVICE_ACCOUNT)

    # Request an access token from the metadata server.
    r = requests.get(url, headers=METADATA_HEADERS)
    r.raise_for_status()

    # Extract the access token from the response.
    try:
        access_token = r.json()['access_token']
        print("get access token success!")
    except Exception as e:
        print("fail to get access token!", e)
        return "fail"
    
    return access_token

def AddGameServer(access_token, gs_username):
    configuration = client.Configuration()
    k8s_host = os.environ.get('k8s_endpoint', 'Specified environment variable is not set.')
    configuration.host = "https://" + k8s_host + ":443"
    configuration.verify_ssl = False
    configuration.api_key = {"authorization": "Bearer " + access_token}
    client.Configuration.set_default(configuration)
    
    # load gameserverallocate template("./localpackage/gameserverallocate.yaml")
    with open(path.join(path.dirname(__file__), "./localpackage/gs.yaml")) as f:
        gameserver_obj = yaml.safe_load(f)
        gameserver_obj['metadata']['name'] = "sd-webui-" + gs_username
        gameserver_obj['metadata']['labels']['user'] = gs_username

    crdclient = client.CustomObjectsApi()

    group = 'agones.dev' # str | the custom resource's group | kubectl api-resources -o wide
    version = 'v1' # str | the custom resource's version
    namespace = 'default' # str | The custom resource's namespace
    plural = 'gameservers' # str | the custom resource's plural name. For TPRs this would be lowercase plural kind. | kubectl api-resources -o wide
    # name = 'demo-allocate' # str | the custom object's name
    # body = None # object | The JSON schema of the Resource to patch.
    
    try:
        response = crdclient.create_namespaced_custom_object(group, version, namespace, plural, body=gameserver_obj)
        gs_name = response['metadata']['name']
    except Exception as e:
        print("failed to create the new sd-webui pod!", e)
        return "fail"
    
    return gs_name

def agones_gs_backend(request): 
    try:
        request_args = request.args
        gs_username = request_args.get('username')
    except Exception as e:
        print(e)
        return json.dumps({'gs_name': 'fail'}), 200, {'ContentType': 'application/json'}
    
    if request_args and gs_username:
        access_token = get_access_token()
        if access_token != "fail":
            response = AddGameServer(access_token, gs_username)
            if response != "fail":
                print("create gameserver success!")
                return json.dumps({'gs_name': response}), 200, {'ContentType': 'application/json'}
            else:
                print("create gameserver fail!")
                return json.dumps({'gs_name': 'fail'}), 200, {'ContentType': 'application/json'}
    else:
        return json.dumps({'gs_name': 'fail'}), 200, {'ContentType': 'application/json'}
