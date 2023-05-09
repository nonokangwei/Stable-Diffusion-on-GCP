import json
import shutil
import requests
import time
import os
from pathlib import Path

sdk_http_port = os.environ['AGONES_SDK_HTTP_PORT']
mount_dir = '/sd_dir'

url = 'http://localhost:' + sdk_http_port + '/watch/gameserver'

time.sleep(30)

r = requests.get(url, stream=True)

if r.encoding is None:
    r.encoding = 'utf-8'

for line in r.iter_lines(decode_unicode=True):
    if line: 
        response = json.loads(line)
        if "user" in response['result']['object_meta']['labels']:
            userid = response['result']['object_meta']['labels']['user']
            print(userid)
            # setup folders here
            if os.path.isdir('/stable-diffusion-webui/outputs'):
                shutil.rmtree('/stable-diffusion-webui/outputs')
            if os.path.isdir('/stable-diffusion-webui/models'):
                shutil.rmtree('/stable-diffusion-webui/models')

            Path(os.path.join(mount_dir, userid, 'outputs')).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(mount_dir, userid, 'inputs')).mkdir(parents=True, exist_ok=True)

            os.symlink(os.path.join(mount_dir, userid, 'outputs'), '/stable-diffusion-webui/outputs', target_is_directory = True)
            os.symlink(os.path.join(mount_dir, userid, 'inputs'), '/stable-diffusion-webui/inputs', target_is_directory = True)
            os.symlink(os.path.join(mount_dir, 'models'), '/stable-diffusion-webui/models', target_is_directory = True)
            
            # webui config files
            Path(os.path.join(mount_dir, userid, 'configs')).mkdir(parents=True, exist_ok=True)
            # config_files_to_link = ['ui-config.json', 'config.json']

            # for file in config_files_to_link:
            #     file_origin = os.path.join('/stable-diffusion-webui', file)
            #     file_to_link = os.path.join(mount_dir, userid, 'configs', file)

            #     if os.path.isfile(file_to_link):
            #         if os.path.isfile(file_origin):
            #             os.remove(file_origin)
            #         os.symlink(file_to_link, file_origin, target_is_directory = False)
            #     elif os.path.isfile(file_origin):
            #         shutil.move(file_origin, file_to_link)
            #         os.symlink(file_to_link, file_origin, target_is_directory = False)
            #     else:
            #         pass
            break