# New Approach

This approach intercepted the calls to `/run/predict/` and `/internal/progress` so that the availability of GameServer and GPU can be conveyed to the enduser. 

## How To

You can use the cloud shell as the run time to do below steps.

This howto is pretty the same as the howto in parent directory, except that: 

- No redis is required.


### Before you begin

1. make sure you have an available GCP project for your deployment
2. Enable the required service API using [cloud shell](https://cloud.google.com/shell/docs/run-gcloud-commands)
```
gcloud services enable compute.googleapis.com artifactregistry.googleapis.com container.googleapis.com file.googleapis.com vpcaccess.googleapis.com redis.googleapis.com cloudscheduler.googleapis.com
```
3. Clone this repo at `~/gcp-stable-diffusion-build-deploy/`
4. `cd ./gcp-stable-diffusion-build-deploy/Stable-Diffusion-UI-Agones/new-approach`

### Create GKE Cluster
do the following step using the cloud shell. This guide using the T4 GPU node as the VM host, by your choice you can change the node type with [other GPU instance type](https://cloud.google.com/compute/docs/gpus).
In this guide we also enabled [Filestore CSI driver](https://cloud.google.com/kubernetes-engine/docs/how-to/persistent-volumes/filestore-csi-driver) for models/outputs sharing.

```
PROJECT_ID=<replace this with your project id>
GKE_CLUSTER_NAME=<replace this with your GKE cluster name>
REGION=<replace this with your region>
VPC_NETWORK=<replace this with your vpc network name>
VPC_SUBNETWORK=<replace this with your vpc subnetwork name>

gcloud beta container --project ${PROJECT_ID} clusters create ${GKE_CLUSTER_NAME} --region ${REGION} \
    --no-enable-basic-auth --cluster-version "1.24.9-gke.3200" --release-channel "None" \
    --machine-type "e2-standard-2" \
    --image-type "COS_CONTAINERD" --disk-type "pd-balanced" --disk-size "100" \
    --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/cloud-platform" \
    --num-nodes "1" --logging=SYSTEM,WORKLOAD --monitoring=SYSTEM --enable-ip-alias \
    --network "projects/${PROJECT_ID}/global/networks/${VPC_NETWORK}" \
    --subnetwork "projects/${PROJECT_ID}/regions/${REGION}/subnetworks/${VPC_SUBNETWORK}" \
    --no-enable-intra-node-visibility --default-max-pods-per-node "110" --no-enable-master-authorized-networks \
    --addons HorizontalPodAutoscaling,HttpLoadBalancing,GcePersistentDiskCsiDriver,GcpFilestoreCsiDriver \
    --autoscaling-profile optimize-utilization

gcloud beta container --project ${PROJECT_ID} node-pools create "gpu-pool" --cluster ${GKE_CLUSTER_NAME} --region ${REGION} --machine-type "custom-4-49152-ext" --accelerator "type=nvidia-tesla-t4,count=1" --image-type "COS_CONTAINERD" --disk-type "pd-balanced" --disk-size "100" --metadata disable-legacy-endpoints=true --scopes "https://www.googleapis.com/auth/cloud-platform" --spot --enable-autoscaling --total-min-nodes "0" --total-max-nodes "6" --location-policy "ANY" --enable-autoupgrade --enable-autorepair --max-surge-upgrade 1 --max-unavailable-upgrade 0 --max-pods-per-node "110" --num-nodes "0"
```

### Get credentials of GKE cluster
```
gcloud container clusters get-credentials ${GKE_CLUSTER_NAME} --region ${REGION}
```

### Install GPU Driver
```
kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml
```

### Create Cloud Artifacts as Docker Repo
```
BUILD_REGIST=<replace this with your preferred Artifacts repo name>

gcloud artifacts repositories create ${BUILD_REGIST} --repository-format=docker \
--location=${REGION}

gcloud auth configure-docker ${REGION}-docker.pkg.dev
```


### Build Stable Diffusion Image
Build image with provided Dockerfile, push to repo in Cloud Artifacts

```
cd gcp-stable-diffusion-build-deploy/Stable-Diffusion-UI-Agones/new-approach/webui
docker build . -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${BUILD_REGIST}/sd-webui-x:0.1
docker push 

```

### Create Filestore
Create Filestore storage, mount and prepare files and folders for models/outputs/training data
You should prepare a VM to mount the filestore instance.

```
FILESTORE_NAME=the-sd-ui-nfs # you can adjust this
FILESTORE_REGION=us-central1 # you can adjust this

VPC_NETWORK=default
FILESHARE_NAME=exports

gcloud filestore instances create ${FILESTORE_NAME} --region=${FILESTORE_REGION} --tier=BASIC_HDD --file-share=name=${FILESHARE_NAME},capacity=1TB --network=name=${VPC_NETWORK}
```
Get the address of the newly created filestore:

```
FS_ADDRESS=$(gcloud filestore instances list --zone ${FILESTORE_REGION} --filter "INSTANCE_NAME: ${FILESTORE_NAME}" --format="value(IP_ADDRESS)")
```

### Install Agones
Install the Agones operator on default-pool, the default pool is long-run node pool that host the Agones Operator.
Note: for quick start, you can using the cloud shell which has helm installed already.
```
helm repo add agones https://agones.dev/chart/stable
helm repo update
helm install sd-agones-release --namespace agones-system -f ./agones/values.yaml agones/agones
```

#### Deal with Agones privilege

After install, make agones roles being aggreated to admin:
```
kubectl label clusterroles agones-allocator rbac.authorization.k8s.io/aggregate-to-admin="true"
kubectl label clusterroles agones-sdk rbac.authorization.k8s.io/aggregate-to-admin="true" 
kubectl label clusterroles agones-controller rbac.authorization.k8s.io/aggregate-to-admin="true" 
```

### Build the proxy image
Build image with provided Dockerfile, push to repo in Cloud Artifacts. Please replace ${REDIS_HOST} in the gcp-stable-diffusion-build-deploy/Stable-Diffusion-UI-Agones/nginx/sd.lua line 15 with the ip address record in previous step.

```
source versions.sh
bash make-image.sh
```

### Deploy PV and PVC

Create the PV and the corresponding PVC

```
cat <<EOF |kubectl apply -f -
apiVersion: v1
kind: PersistentVolume
metadata:
  name: nfs
  labels:
    app: ngx-scheduler
spec:
  capacity:
    storage: 1000Gi
  accessModes:
    - ReadWriteMany
  nfs:
    server: ${FS_ADDRESS}
    path: "/exports"

EOF

kubectl apply -f pv-pvcs.yaml
```


### Deploy stable-diffusion agones deployment
Deploy stable-diffusion agones deployment, please replace the image URL in the deployment.yaml and fleet yaml with the image built before.
```
kubectl apply -f fleet.yaml
kubectl apply -f ../agones/fleet_autoscale.yaml
```



### Deploy IAP(identity awared proxy)
To allocate isolated stable-diffusion runtime and provide user access auth capability, using the Google Cloud IAP service as an access gateway to provide the identity check and prograge the idenity to the stable-diffusion backend.

Config the OAuth consent screen and OAuth credentials, check out the [guide](https://cloud.google.com/iap/docs/enabling-kubernetes-howto#oauth-configure).

Create an static external ip address, record the ip address.
```
gcloud compute addresses create sd-agones --global
gcloud compute addresses describe sd-agones --global --format=json | jq .address
```

Config BackendConfig, replace the client_id and client_secret with the OAuth client create before.
```
kubectl create secret generic iap-secret --from-literal=client_id=client_id_key \
    --from-literal=client_secret=client_secret_key
```

### Deploy the_proxy
Change the DOMAIN_NAME1 in managed-cert.yaml with the environment domain, then deploy the depend resources.
Also change the Image URL in the deployment
```
kubectl apply -f the-proxy-sche.yaml
```

Give the authorized users required priviledge to access the service. [Guide](https://cloud.google.com/iap/docs/enabling-kubernetes-howto#iap-access)

