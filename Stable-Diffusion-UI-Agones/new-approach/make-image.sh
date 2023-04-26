#!/bin/bash
. versions.sh
cd pyapp
docker build . -t $REG/py-gpu-sche:$TAG
docker push $REG/py-gpu-sche:$TAG
cd -
