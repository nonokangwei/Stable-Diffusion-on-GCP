#!/bin/bash
python3 user-watch.py &
python3 launch.py --listen --xformers --enable-insecure-extension-access --no-gradio-queue