#[agones version start]#######
locals {
  project_id          = "PROJECT_ID"
  oauth_client_id     = "OAUTH_CLIENT_ID"
  oauth_client_secret = "OAUTH_CLIENT_SECRET"
  sd_webui_domain     = "YOUR_OWNED_CUSTOM_DOMAIN_OR_SUBDOMAIN"
  region              = "us-central1"
  filestore_zone      = "us-central1-f" # Filestore location must be same region or zone with gke
  cluster_location    = "us-central1-f" # GKE Cluster location
  node_machine_type   = "custom-12-49152-ext"
  accelerator_type    = "nvidia-tesla-t4" # Available accelerator_type from gcloud compute accelerator-types list --format='csv(zone,name)'
  gke_num_nodes       = 1
}

module "agones_gcp_res" {
  source                          = "./modules/agones/gcp-res"
  project_id                      = local.project_id
  region                          = local.region
  filestore_zone                  = local.filestore_zone
  cluster_location                = local.cluster_location
  node_machine_type               = local.node_machine_type
  accelerator_type                = local.accelerator_type
  gke_num_nodes                   = local.gke_num_nodes
  cloudfunctions_source_code_path = "../Stable-Diffusion-UI-Agones/cloud-function/"
}

module "agones_build_image" {
  source            = "./modules/agones/cloud-build"
  artifact_registry = module.agones_gcp_res.artifactregistry_url
}

module "helm_agones" {
  source               = "./modules/agones/helm-agones"
  project_id           = local.project_id
  gke_cluster_name     = module.agones_gcp_res.kubernetes_cluster_name
  gke_cluster_location = module.agones_gcp_res.gke_location
  gke_cluster_nodepool = module.agones_gcp_res.gpu_nodepool_name
}

module "agones_k8s_res" {
  source                             = "./modules/agones/k8s-res"
  project_id                         = local.project_id
  oauth_client_id                    = local.oauth_client_id
  oauth_client_secret                = local.oauth_client_secret
  sd_webui_domain                    = local.sd_webui_domain
  gke_cluster_name                   = module.agones_gcp_res.kubernetes_cluster_name
  gke_cluster_location               = module.agones_gcp_res.gke_location
  gke_cluster_nodepool               = module.agones_gcp_res.gpu_nodepool_name
  google_filestore_reserved_ip_range = module.agones_gcp_res.google_filestore_reserved_ip_range
  webui_address_name                 = module.agones_gcp_res.webui_address_name
  nginx_image_url                    = module.agones_build_image.nginx_image
  webui_image_url                    = module.agones_build_image.webui_image
  game_server_image_url              = module.agones_build_image.game_server_image
}

output "webui_ingress_address" {
  value       = module.agones_gcp_res.webui_address
  description = "webui ip address for ingress"
}

#[agones version end]#

#---seperate block---

#[gke version start]#

locals {
  project_id          = "PROJECT_ID"
  region              = "us-central1"
  filestore_zone      = "us-central1-b" # Filestore location must be same region or zone with gke
  cluster_location    = "us-central1-b" # GKE Cluster location
  node_machine_type   = "custom-12-49152-ext"
  accelerator_type    = "nvidia-tesla-t4" # Available accelerator_type from gcloud compute accelerator-types list --format='csv(zone,name)'
  gke_num_nodes       = 1
}

module "nonagones_gcp_res" {
  source            = "./modules/nonagones/gcp-res"
  project_id        = local.project_id
  region            = local.region
  filestore_zone    = local.filestore_zone
  cluster_location  = local.cluster_location
  node_machine_type = local.node_machine_type
  accelerator_type  = local.accelerator_type
  gke_num_nodes     = local.gke_num_nodes
}

module "nonagones_build_image" {
  source            = "./modules/nonagones/cloud-build"
  artifact_registry = module.nonagones_gcp_res.artifactregistry_url
}

module "nonagones_k8s_res" {
  source                             = "./modules/nonagones/k8s-res"
  project_id                         = local.project_id
  gke_cluster_name                   = module.nonagones_gcp_res.kubernetes_cluster_name
  gke_cluster_location               = local.cluster_location
  gke_cluster_nodepool               = module.nonagones_gcp_res.gpu_nodepool_name
  google_filestore_reserved_ip_range = module.nonagones_gcp_res.google_filestore_reserved_ip_range
  webui_image_url                    = module.nonagones_build_image.webui_image
}

#[gke version end]