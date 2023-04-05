#!/bin/bash
cd /app
mv kubectl /usr/bin/kubectl
chmod +x /usr/bin/kubectl
gunicorn -t 0 --workers=5 the_proxy:app -b 0:8080
