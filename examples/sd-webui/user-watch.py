import json
import shutil
import requests
import time
import os
import signal
import subprocess
from pathlib import Path

def restart_proc():
    cmd_str = """ps -ef | grep python | egrep 'webui.py|launch.py' | grep -v grep"""
    try:    
        # iterating through each instance of the process
        for line in os.popen(cmd_str):
            fields = line.split()
                
            # extracting Process ID from the output
            pid = fields[1]
                
            # terminating process
            print(int(pid), signal.SIGKILL)
            os.kill(int(pid), signal.SIGKILL)
        print("Process Successfully terminated")         
    except:
        print("Error Encountered while killing existing process")

    os.chdir('/stable-diffusion-webui/')
    cmd_str = "python webui.py --xformers --medvram --listen --enable-insecure-extension-access"
    p = subprocess.Popen(cmd_str, preexec_fn=os.setsid, shell=True)
    print("pid = ", p.pid)
    time.sleep(30)
    print("parent exit")
    return


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
            # if os.path.isdir('/stable-diffusion-webui/models'):
            #     shutil.rmtree('/stable-diffusion-webui/models')

            Path(os.path.join(mount_dir, userid, 'outputs')).mkdir(parents=True, exist_ok=True)
            Path(os.path.join(mount_dir, userid, 'inputs')).mkdir(parents=True, exist_ok=True)

            os.symlink(os.path.join(mount_dir, userid, 'outputs'), '/stable-diffusion-webui/outputs', target_is_directory = True)
            os.symlink(os.path.join(mount_dir, userid, 'inputs'), '/stable-diffusion-webui/inputs', target_is_directory = True)
            # os.symlink(os.path.join(mount_dir, 'models'), '/stable-diffusion-webui/models', target_is_directory = True)
            
            # webui config files
            Path(os.path.join(mount_dir, userid, 'ui-configs')).mkdir(parents=True, exist_ok=True)
            
            config_files_to_link = ['ui-config.json', 'config.json']
            
            for file in config_files_to_link:
                file_origin = os.path.join('/stable-diffusion-webui', file)
                file_dest = os.path.join(mount_dir, userid, 'ui-configs', file)
                if os.path.isfile(file_origin) and not os.path.isfile(file_dest):
                    shutil.copy2(file_origin, file_dest)
                if os.path.isfile(file_dest):
                    os.remove(file_origin)
                    os.symlink(file_dest, file_origin, target_is_directory = False)

            restart_proc()
            break