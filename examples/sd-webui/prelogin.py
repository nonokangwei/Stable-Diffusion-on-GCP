import json
import shutil
import requests
import time
import os
from pathlib import Path

mount_dir = '/sd_dir'

if os.path.isdir('/stable-diffusion-webui/models'):
    shutil.rmtree('/stable-diffusion-webui/models')

os.symlink(os.path.join(mount_dir, 'models'), '/stable-diffusion-webui/models', target_is_directory = True)