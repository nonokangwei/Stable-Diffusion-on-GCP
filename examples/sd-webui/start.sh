#!/bin/bash
python3 prelogin.py
python3 user-watch.py
python3 webui.py --listen --xformers --medvram --enable-insecure-extension-access