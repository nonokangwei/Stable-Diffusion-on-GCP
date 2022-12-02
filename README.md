# Stable-Diffusion on Google Cloud Quick Start Guide

This guide give simple steps for stable-diffusion users to launch a stable diffusion deployment by using GCP GKE servce, Cloud Build, Cloud Deploy service. User can just follow the step have your stable diffusion model running.

* [Introduction](#Introduction)
* [How-To](#how-to)

## Introduction
   This project is using the [Stable-Diffusion-WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) open source as the user interactive front-end, customer can just prepare the stable diffusion model to build/deployment stable diffusion model by container. This project use the cloud build to help you quick build up a docker image with your stable diffusion model, then you can make a deployment base on the docker image.

## How To
you can use the cloud shell as the run time to do below steps.
### Before you begin
1. make sure you have an available GCP project for your deployment
2. Enable the required service API using [cloud shell](https://cloud.google.com/shell/docs/run-gcloud-commands)
```
gcloud services enable compute.googleapis.com artifactregistry.googleapis.com container.googleapis.com cloudbuild.googleapis.com clouddeploy.googleapis.com storage.googleapis.com
```
### Create GKE Cluster
do the following step using the cloud shell. This guide using the A100 GPU node as the VM host, by your choice you can change the node type with [other GPU instance type](https://cloud.google.com/compute/docs/gpus).
```
PROJECT_ID=<replace this with your project id>
GKE_CLUSTER_NAME=<replace this with your GKE cluster name>
REGION=<replace this with your region>

gcloud beta container --project $PROJECT_ID clusters create $GKE_CLUSTER_NAME --zone "${REGION}-b" --no-enable-basic-auth --cluster-version "1.23.12-gke.100" --release-channel "regular" --machine-type "a2-highgpu-1g" --accelerator "type=nvidia-tesla-a100,count=1" --image-type "COS_CONTAINERD" --disk-type "pd-standard" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/devstorage.read_only","https://www.googleapis.com/auth/logging.write","https://www.googleapis.com/auth/monitoring","https://www.googleapis.com/auth/servicecontrol","https://www.googleapis.com/auth/service.management.readonly","https://www.googleapis.com/auth/trace.append" --max-pods-per-node "110" --spot --num-nodes "1" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-ip-alias --network "projects/${PROJECT_ID}/global/networks/default" --subnetwork "projects/${PROJECT_ID}/regions/${REGION}/subnetworks/default" --no-enable-intra-node-visibility --default-max-pods-per-node "110" --no-enable-master-authorized-networks --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --enable-shielded-nodes --node-locations "${REGION}-b"
```

### Install GPU Driver on GKE
```
gcloud container clusters get-credentials ${GKE_CLUSTER_NAME} --region ${REGION}-b 
```


### Create Cloud Artifacts as Docker Repo
```
BUILD_REGIST=<replace this with your preferred Artifacts repo nmae>

gcloud artifacts repositories create quickstart-docker-repo --repository-format=docker \
--location=${REGION} --description="Stable Diffusion Docker repository"
```

### Create Cloud Build Trigger
```
##(need to change to CloudMoma Git Repo Address)
BUILD_REPO=https://github.com/nonokangwei/gcp-stable-diffusion-build-deploy.git

echo -n "webhooksecret" | gcloud secrets create webhook-secret \
    --replication-policy="automatic" \
    --data-file=-

git clone ${BUILD_REPO}

cd gcp-stable-diffusion-build-deploy/

gcloud alpha builds triggers create webhook --name=stable-diffusion-build-trigger --inline-config=clouddeploy.yaml --secret=projects/${PROJECT_ID}/secrets/webhook-secret/versions/1
```

### Prepare Stable Diffusion Model
one of the public available Stable Diffusion model is [HuggingFace](https://huggingface.co/runwayml/stable-diffusion-v1-5), register an id and download the .ckpt file, then upload to the GCS bucket.

```
BUILD_BUCKET=<replace this with your bucket name>
gcloud storage buckets create gs://${BUCKET_NAME} --location=${REGION}
```

Suggest you can refer the GCS path pattern gs://${BUCKET_NAME}/${MODEL_NAME}/model.ckpt. ${MODEL_NAME} can name like stablediffusion.

[Guide](https://cloud.google.com/storage/docs/uploading-objects) of upload file to the GCS bucket path you create. 

### Build Stable Diffusion Image
Get cloud build trigger url: [How-To](https://cloud.google.com/build/docs/automate-builds-webhook-events), in GCloud Console findout the Cloud Build Trigger that created before, Preview the trigger URL

trigger the build 
```
MODEL_NAME=<replace this with your model name>
BUILD_TRIGGER_URL=<replace this with the url you get>

 curl -X POST -H "application/json" ${BUILD_TRIGGER_URL} -d '{"message": {"buildrepo": ${BUILD_REPO}, "buildbucket": ${BUILD_BUCKET}, "buildmodel": ${MODEL_NAME}, "buildregist": ${BUILD_REGIST}}}'
```




