#!/bin/bash
. versions.sh
cd pyapp
gcloud --project $PROJECT_ID builds submit . -t $REG/py-gpu-sche:$TAG
#docker push $REG/py-gpu-sche:$TAG
cd -
