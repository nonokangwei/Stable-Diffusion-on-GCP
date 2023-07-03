import json
import shutil
import requests
import time
import os

sdk_http_port = os.environ['AGONES_SDK_HTTP_PORT']

url = 'http://localhost:' + sdk_http_port + '/watch/gameserver'

time.sleep(30)

r = requests.get(url, stream=True)

if r.encoding is None:
    r.encoding = 'utf-8'

for line in r.iter_lines(decode_unicode=True):
    if line:
        response = json.loads(line)
        if "user" in response['result']['object_meta']['labels']:
            print(response['result']['object_meta']['labels']['user'])
            if os.path.isdir('/stable-diffusion-webui/outputs'):
                shutil.rmtree('/stable-diffusion-webui/outputs')
            src = '/result/' + response['result']['object_meta']['labels']['user'] + '/outputs'
            if os.path.isdir(src):
                os.symlink(src, '/stable-diffusion-webui/outputs', target_is_directory = True)
                break
            else :
                os.makedirs(src)
                os.symlink(src, '/stable-diffusion-webui/outputs', target_is_directory = True)
                break
