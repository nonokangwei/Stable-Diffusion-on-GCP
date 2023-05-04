# Infrastructure and kubernetes resource deploy guide

We Offer two version deployment of Stable Diffusion Web UI on GKE

##  Agones Version
### 01 Set up permissions

Make sure that you have the necessary permissions on your user account:

- ROLE: roles/artifactregistry.admin

- ROLE: roles/compute.admin

- ROLE: roles/compute.instanceAdmin.v1

- ROLE: roles/compute.networkAdmin

- ROLE: roles/container.admin

- ROLE: roles/file.editor

**roles/editor or roles/owner** is prefered

### 02 Replace project parameter

edit the main.tf replace the locals parameter with your project's.
- If you choose regional cluster replace the location parameter with region code
- If you choose zonal cluster replace the location parameter with zone code

follow example of us-central1-f zonal cluster

```bash
locals {
  project_id     = "PROJECT_ID"
  region         = "us-central1"
  filestore_zone = "us-central1-f"
  location       = "us-central1-f"
  gke_num_nodes  = 1
}

```
### 03 Provision Infrastructure (VPC | Subnet | NAT | FileStore | Artifact Registry | GKE | Firewall Rule | Redis | Redis Private DNS | VPC Connector | Cloud Function | Scheduler | GCS Bucket for Cloud Function Code  )

```bash
# switch to work directory
cd gcp-stable-diffusion-build-deploy/terraform-provision-infra/agones-version

# init terraform
terraform init

# deploy Infrastructure
terraform plan
terraform apply -auto-approve

# destroy Infrastructure
terraform destroy -auto-approve
```
### 04 Manual Step includes Config IAP refer to [Link](https://cloud.google.com/iap/docs/enabling-kubernetes-howto#oauth-configure) and create a DNS A record point to reserved IP (from terraform output webui_address) 
Main step as follow
1. Configuring the OAuth consent screen
2. Creating OAuth credentials (**IMPORTANT** *please make note of client id and secret**)
3. Update OAuth client Authorized redirect URIs
4. Creating A recored point to webui_address in DNS provider (sdwebui.example.com - > xxx.xxx.xxx.xxx)
5. (After kubernetes resource has been created)Grant IAP-secured Web App User permission for user


### 05 Replace OAuth Client id and secret and your owned domain in  kubernetes.tf file

```bash
locals {
  oauth_client_id  = "OAUTH_CLIENT_ID"
  oauth_client_secret = "OAUTH_CLIENT_SECRET"
  sd_webui_domain = "your_owned_domain_or_subdomain"
}
```

### 06 Deploy  Kubernetes sample resource (GKE FileStore PV and PVC | Kubernetes Secret | Kubernetes Namespace |Agones| GPU Driver |Stackdriver Adapter|Nginx_deployment|Fleet|Fleet Autoscaler|IAP Ingress )

```bash
# switch to kubernetes sample directory
cd gcp-stable-diffusion-build-deploy/terraform-provision-infra/agones-version/kubernetes-deployment

# init terraform
terraform init

# deploy Infrastructure
terraform plan
terraform apply -auto-approve

# destroy Infrastructure
terraform destroy -auto-approve
```

### 07 Grant Permission and access web ui
* Back to Step 04.5 grant IAP-secured Web App User permission 
* Access webui via your domain or subdomain


## No Agones Version

### 01 Set up permissions

Make sure that you have the necessary permissions on your user account:

- ROLE: roles/artifactregistry.admin

- ROLE: roles/compute.admin

- ROLE: roles/compute.instanceAdmin.v1

- ROLE: roles/compute.networkAdmin

- ROLE: roles/container.admin

- ROLE: roles/file.editor

**roles/editor or roles/owner** is prefered

### 02 Replace project parameter

edit the main.tf replace the locals parameter with your project's.
- If you choose regional cluster replace the location parameter with region code
- If you choose zonal cluster replace the location parameter with zone code

follow example of us-central1-f zonal cluster

```bash
locals {
  project_id      = "PROJECT_ID"
  region          = "us-central1"
  location        = "us-central1-f"
  gke_num_nodes   = 1
}

```
### 03 Provision Infrastructure (VPC | Subnet | NAT | FileStore | Artifact Registry | GKE  )

```bash
# switch to work directory
gcp-stable-diffusion-build-deploy/terraform-provision-infra/non-agones-version

# init terraform
terraform init

# deploy Infrastructure
terraform plan
terraform apply -auto-approve

# destroy Infrastructure
terraform destroy -auto-approve
```

### 04 Deploy  Kubernetes sample deployment (GKE FileStore PV and PVC | GPU Driver | SD deployment | SD Service LB )

```bash
# switch to kubernetes sample directory
cd gcp-stable-diffusion-build-deploy/terraform-provision-infra/non-agones-version/kubernetes-sample

# init terraform
terraform init

# deploy Infrastructure
terraform plan
terraform apply -auto-approve

# Get SD Web UI LB IP 
kubectl get ingress

# destroy Infrastructure
terraform destroy -auto-approve
```
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
