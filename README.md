# Stable Diffusion on Google Cloud Quick Start Guide

This guide provides you simple steps to deploy a Stable Diffusion solution in your Google Cloud Project, utilising Google Cloud's products and open source solutions.

| Folder                             | Description                                                                                                                                                                                                                                                                                   |
|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [Stable-Diffusion-UI-Novel](./Stable-Diffusion-UI-Novel) | This contains all the YAML files and Dockerfiles for deploying Stable Diffusion using CLI. |
| [terraform-provision-infra](./terraform-provision-infra) | This contains all the Terraform scripts and resources to create the infrastructure that the project relies on. 
| [Training](./Training)             | Contains the code for training DreamBooth on Vertex AI                                                                              | 

## Introduction
   This project uses the open source [Stable-Diffusion-WebUI](https://github.com/AUTOMATIC1111/stable-diffusion-webui) as the user interface. Customer can build and deploy Stable Diffusion model into container. This project uses Cloud Build to help you quickly build a docker image with your Stable Diffusion model, then you can create a deployment based on the docker image. 

   Projects and products utilised include:
*   [GKE](https://cloud.google.com/kubernetes-engine) for hosting Stable Diffusion and attaching GPU hardware to nodes in your Kubernetes cluster.
*   [Filestore](https://cloud.google.com/filestore) for saving models and output files.
*   [Vertex AI](https://cloud.google.com/vertex-ai) for training and fine-tuning the model.
*   [Cloud Build](https://cloud.google.com/build) for building images and Continuous Integration.
*   [GKE](https://cloud.google.com/kubernetes-engine) Standard clusters running [Agones](https://agones.dev/) for isolating runtime for different users and scaling.
*   [Stable Diffusion](https://huggingface.co/runwayml/stable-diffusion-v1-5) for generating images from text.
*   [Webui](https://github.com/AUTOMATIC1111/stable-diffusion-webui): A browser interface for Stable Diffusion.

## Architecture
![Architecture](./assets/sd_gke_01.drawio.png)

* Architecture GKE + GPU + spot + Vertex AI custom training
* No conflicts for multiple users, one deployment per model, use different mount point to distinguish models
* Scaling with HPA with GPU metrics, supports GPU time sharing
* Inference and training on WebUI
* Dreambooth Training on Vertex AI
* Optimized for vram saving, Inference+Training can be done in a T4 GPU
* No intrusive change against AUTOMATIC1111 webui, easy to upgrade or install extensions with Dockerfile

## Run in Your Google Cloud Project

> **Warning**
> This solution in its default state creates a Kubernetes cluster with one GPU. Running it for an extended amount of time may incur significant costs.

### Before you begin
To deploy this solution, you will need the following applications installed on your workstation. If you use Cloud Shell to run these steps, those applications are already installed for you:
* A Google Cloud Project with a VPC network
* [Terraform](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli)
* [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)

You can also click on the following icon to open this repository in a [Google Cloud Shell](https://cloud.google.com/shell) web development environment.

[![Open in Cloud Shell](https://gstatic.com/cloudssh/images/open-btn.svg)](https://ssh.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/nonokangwei/Stable-Diffusion-on-GCP.git&cloudshell_tutorial=README.md)

## Enable APIs
Start a [Cloud Shell](https://cloud.google.com/shell/docs/run-gcloud-commands) instance to perform the following steps.

In Cloud Shell, enable the required Cloud APIs using the [gcloud CLI](https://cloud.google.com/sdk/docs).
```
gcloud services enable compute.googleapis.com artifactregistry.googleapis.com container.googleapis.com file.googleapis.com
```

## Initialize the environment
In Cloud Shell, set the default Compute Engine zone to the zone where you are going to create your GKE cluster.
```shell
export PROJECT=$(gcloud info --format='value(config.project)')
export GKE_CLUSTER_NAME=<the name of your new cluster>
export REGION=<the desired region for your cluster, such as us-central1>
export ZONE=<the desired zone for your node pool, such as us-central1-a. The zone must be in the same region as the cluster control plane>
export VPC_NETWORK=<the name of your VPC network>
export VPC_SUBNETWORK=<the name of your subnetwork>
export CLIENT_PER_GPU=<the maximum number of containers that will share each physical GPU, valid number is 2 or 3>
export BUILD_REGIST=<your desired Artifacts repository name>
```

## Create GKE Cluster
The below command creates a GKE standard cluster with [NVIDIA T4](https://www.nvidia.com/en-us/data-center/tesla-t4/) GPU. GKE standard clusters support all [GPU  types](https://cloud.google.com/compute/docs/gpus) that are supported by Compute Engine, therefore you can adjust the configuration and choose the appropriate GPU type based on the resource needs of your workload. We will also enable the [Filestore CSI driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver) for saving and sharing models and output files. Furthermore, We will also utilise the [GPU time-sharing](https://cloud.google.com/kubernetes-engine/docs/how-to/timesharing-gpus#enable-cluster) feature in GKE to let you more efficiently use your attached GPUs and save running costs.

In our example, we will use a custom intance type which is 4c48Gi, since we are going to assign 2c22Gi to each pod.

**NOTE: If you are creating a private GKE cluster, create [Cloud NAT gateway](https://cloud.google.com/nat/docs/gke-example#create-nat) to ensure that you node pool has access to the internet.**

```shell
#[option A] gcloud example for creating a regional cluster with high availability
gcloud beta container --project ${PROJECT_ID} clusters create ${GKE_CLUSTER_NAME} --region ${REGION} \
    --no-enable-basic-auth --cluster-version "1.24.9-gke.3200" --release-channel "None" \
    --machine-type "custom-4-49152-ext" --accelerator "type=nvidia-tesla-t4,count=1,gpu-sharing-strategy=time-sharing,max-shared-clients-per-gpu=${CLIENT_PER_GPU}" \
    --image-type "COS_CONTAINERD" --disk-type "pd-balanced" --disk-size "100" \
    --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/cloud-platform" \
    --num-nodes "1" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-private-nodes \
    --master-ipv4-cidr "172.16.1.0/28" --enable-ip-alias --network "projects/${PROJECT_ID}/global/networks/${VPC_NETWORK}" \
    --subnetwork "projects/${PROJECT_ID}/regions/${REGION}/subnetworks/${VPC_SUBNETWORK}" \
    --no-enable-intra-node-visibility --default-max-pods-per-node "110" --no-enable-master-authorized-networks \
    --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver,GcpFilestoreCsiDriver \
    --enable-autoupgrade --no-enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 \
    --enable-autoprovisioning --min-cpu 1 --max-cpu 64 --min-memory 1 --max-memory 256 \
    --autoprovisioning-scopes=https://www.googleapis.com/auth/cloud-platform --no-enable-autoprovisioning-autorepair \
    --enable-autoprovisioning-autoupgrade --autoprovisioning-max-surge-upgrade 1 --autoprovisioning-max-unavailable-upgrade 0 \
    --enable-vertical-pod-autoscaling --enable-shielded-nodes


#[option B] gcloud example for creating a zonal cluster
gcloud beta container --project ${PROJECT_ID} clusters create ${GKE_CLUSTER_NAME} --zone ${ZONE} \
    --no-enable-basic-auth --cluster-version "1.24.9-gke.3200" --release-channel "None" \
    --machine-type "custom-4-49152-ext" --accelerator "type=nvidia-tesla-t4,count=1,gpu-sharing-strategy=time-sharing,max-shared-clients-per-gpu=${CLIENT_PER_GPU}" \
    --image-type "COS_CONTAINERD" --disk-type "pd-balanced" --disk-size "100" \
    --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/cloud-platform" \
    --num-nodes "1" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-private-nodes \
    --master-ipv4-cidr "172.16.1.0/28" --enable-ip-alias --network "projects/${PROJECT_ID}/global/networks/${VPC_NETWORK}" \
    --subnetwork "projects/${PROJECT_ID}/regions/${REGION}/subnetworks/${VPC_SUBNETWORK}" \
    --no-enable-intra-node-visibility --default-max-pods-per-node "110" --no-enable-master-authorized-networks \
    --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver,GcpFilestoreCsiDriver \
    --enable-autoupgrade --no-enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 \
    --enable-autoprovisioning --min-cpu 1 --max-cpu 64 --min-memory 1 --max-memory 256 \
    --autoprovisioning-scopes=https://www.googleapis.com/auth/cloud-platform --no-enable-autoprovisioning-autorepair \
    --enable-autoprovisioning-autoupgrade --autoprovisioning-max-surge-upgrade 1 --autoprovisioning-max-unavailable-upgrade 0 \
    --enable-vertical-pod-autoscaling --enable-shielded-nodes
```

## Create NAT and Cloud Router (Optional if your cluster is not private)
```shell
# create cloud router
gcloud compute routers create nat-router --network ${VPC_NETWORK} --region ${REGION}

# create nat 
gcloud compute routers nats create nat-gw --router=nat-router --region ${REGION} --auto-allocate-nat-external-ips --nat-all-subnet-ip-ranges
```

### Connect to your GKE cluster
```shell
# For regional cluster
gcloud container clusters get-credentials ${GKE_CLUSTER_NAME} --region ${REGION}

# For zonal cluster
gcloud container clusters get-credentials ${GKE_CLUSTER_NAME} ---zone ${ZONE}
```

## Install NVIDIA GPU device drivers
After creating a GKE cluster with GPU, you need to install NVIDIA's device drivers on the nodes. Google provides a DaemonSet that you can apply to install the drivers. To deploy the installation [DaemonSet](https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml) and install the default GPU driver version, run the following command:
```shell
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

## Create Cloud Artifacts as Docker Repo
```
BUILD_REGIST=<replace this with your preferred Artifacts repo name>

gcloud artifacts repositories create ${BUILD_REGIST} --repository-format=docker \
--location=${REGION}

```

## Build Stable Diffusion Image
Build image with provided Dockerfile, push to repo in Cloud Artifacts \
Please note I have prepared two seperate Dockerfiles for inference and training, for inference, we don't include dreambooth extension for training.

```shell
cd gcp-stable-diffusion-build-deploy/Stable-Diffusion-UI-Novel/docker_inference

# Build Docker image locally (machine with at least 8GB memory avaliable)
gcloud auth configure-docker ${REGION}-docker.pkg.dev
docker build . -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${BUILD_REGIST}/sd-webui:inference
docker push 

# Build image with Cloud Build
gcloud builds submit --machine-type=e2-highcpu-32 --disk-size=100 --region=${REGION} -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${BUILD_REGIST}/sd-webui:inference 

```

## Create a Filestore instance
Use the below commands to create a Filestore instance to store model outputs and training data.

**NOTE: models/Stable-Diffusion/ folder is not empty. Mounting the Filestore file share directly will lose some folders and introduce error. One way to avoid this is to mount the Filestore file share, copy the folders from repo's models/Stable-Diffusion/ before being used by pods.**

```
FILESTORE_NAME=<replace with filestore instance name>
FILESTORE_ZONE=<replace with filestore instance zone>
FILESHARE_NAME=<replace with filestore share name>

gcloud filestore instances create ${FILESTORE_NAME} --zone=${FILESTORE_ZONE} --tier=BASIC_HDD --file-share=name=${FILESHARE_NAME},capacity=1TB --network=name=${VPC_NETWORK}
```

## Configure Cluster Autoscaling
Enable autoscaling for your node pool to automatically resize the number of nodes in your node pool, based on the demands of your workloads. When the horizonal pod autocale feature scale up the pod replica size, it will trigger the node pool to scale out to provide required GPU resource. 

```shell
# For regional cluster
gcloud container clusters update ${GKE_CLUSTER_NAME} --enable-autoscaling --node-pool=default-pool --min-nodes=0 --max-nodes=5 --region=${REGION}

# For zonal cluster
gcloud container clusters update ${GKE_CLUSTER_NAME} --enable-autoscaling --node-pool=default-pool --min-nodes=0 --max-nodes=5 ---zone ${ZONE}
```

## Enable Horizonal Pod autoscaling(HPA)
The [Horizontal Pod Autoscaler](https://cloud.google.com/kubernetes-engine/docs/concepts/horizontalpodautoscaler) changes the shape of your Kubernetes workload by automatically increasing or decreasing the number of Pods in response to the workload's CPU or memory consumption, or in response to custom metrics reported from within Kubernetes or external metrics from sources outside of your cluster.
Install the stackdriver adapter to enable the stable-diffusion deployment scale with GPU usage metrics.

```shell
# Optional, just to ensure that you have necessary permissons to perform the following actions on the cluster
kubectl create clusterrolebinding cluster-admin-binding --clusterrole cluster-admin --user "$(gcloud config get-value account)"

kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/k8s-stackdriver/master/custom-metrics-stackdriver-adapter/deploy/production/adapter_new_resource_model.yaml
```

Deploy horizonal pod autoscaler policy on the Stable Diffusion deployment
```
kubectl apply -f ./Stable-Diffusion-UI-Novel/kubernetes/hpa.yaml
```
**Note: If the GPU time-sharing feature is enabled in GKE clsuter, please use the hpa-timeshare.yaml, make sure to substitude the GKE_CLUSTER_NAME in the YAML file.**

## Other notes
### About multi-users/sessions
AUTOMATIC1111's Stable Diffusion WebUI does not support multi users/sessions at this moment, you can refer to https://github.com/AUTOMATIC1111/stable-diffusion-webui/issues/7970. To support multi-users, we create one deployment for each model.

### About file structure
Instead of building images for each model, we use one image with shared storage from Filestore and properly orchestrate for our files and folders.
Please refer to the deployment_*.yaml for reference.

Your folder structure could probably look like this in your Filestore file share:
```
/models/Stable-diffusion # <--- This is where Stable Diffusion WebUI looking for models
|-- nai
|   |-- nai.ckpt
|   |-- nai.vae.pt
|   `-- nai.yaml
|-- sd15
|   `-- v1-5-pruned-emaonly.safetensors

/inputs/ # <--- for training images, only use it when running training job from UI(sd_dreammbooth_extension)
|-- alvan-nee-cropped
|   |-- alvan-nee-9M0tSjb-cpA-unsplash_cropped.jpeg
|   |-- alvan-nee-Id1DBHv4fbg-unsplash_cropped.jpeg
|   |-- alvan-nee-bQaAJCbNq3g-unsplash_cropped.jpeg
|   |-- alvan-nee-brFsZ7qszSY-unsplash_cropped.jpeg
|   `-- alvan-nee-eoqnr8ikwFE-unsplash_cropped.jpeg

/outputs/ # <--- for generated images
|-- img2img-grids
|   `-- 2023-03-14
|       |-- grid-0000.png
|       `-- grid-0001.png
|-- img2img-images
|   `-- 2023-03-14
|       |-- 00000-425382929.png
|       |-- 00001-631481262.png
|       |-- 00002-1301840995.png
```
