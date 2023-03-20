# Got a bunch of .ckpt files to convert?
# Here's a handy script to take care of all that for you!
# Original .ckpt files are not touched!
# Make sure you have enough disk space! You are going to DOUBLE the size of your models folder!
#
# First, run:
# pip install torch torchsde==0.2.5 safetensors==0.2.5
#
# Place this file in the **SAME DIRECTORY** as all of your .ckpt files, open a command prompt for that folder, and run:
# python convert_to_safe.py

import os
import torch
from safetensors.torch import save_file

files = os.listdir()
for f in files:
    if f.lower().endswith('.ckpt'):
        print(f'Loading {f}...')
        fn = f"{f.replace('.ckpt', '')}.safetensors"

        if fn in files:
            print(f'Skipping, as {fn} already exists.')
            continue

        try:
            with torch.no_grad():
                weights = torch.load(f)["state_dict"]
                if "state_dict" in weights:
                    weights.pop("state_dict")
                fn = f"{f.replace('.ckpt', '')}.safetensors"
                print(f'Saving {fn}...')
                save_file(weights, fn)
        except Exception as ex:
            print(f'ERROR converting {f}: {ex}')

print('Done!')