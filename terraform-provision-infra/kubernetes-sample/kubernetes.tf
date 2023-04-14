terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.19.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "3.2.1"
    }
    google = {
      source  = "hashicorp/google"
      version = "4.60.1"
    }
  }
}
data "terraform_remote_state" "gke" {
  backend = "local"

  config = {
    path = "../terraform.tfstate"
  }
}

# Configure kubernetes provider with Oauth2 access token.
# https://registry.terraform.io/providers/hashicorp/google/latest/docs/data-sources/client_config
# This fetches a new token, which will expire in 1 hour.
data "google_client_config" "default" {}

data "google_container_cluster" "my_cluster" {
  project  = data.terraform_remote_state.gke.outputs.project_id
  name     = data.terraform_remote_state.gke.outputs.kubernetes_cluster_name
  location = data.terraform_remote_state.gke.outputs.gke_location
}

provider "kubernetes" {
  host                   = "https://${data.terraform_remote_state.gke.outputs.kubernetes_cluster_host}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(data.google_container_cluster.my_cluster.master_auth[0].cluster_ca_certificate)
}

resource "kubernetes_storage_class" "nfs" {
  metadata {
    name = "filestore"
  }
  reclaim_policy      = "Retain"
  storage_provisioner = "nfs"
}

resource "kubernetes_persistent_volume_v1" "nfs_pv" {
  metadata {
    name = "filestore-nfs-pv"
  }
  spec {
    capacity = {
      storage = "1Ti"
    }
    storage_class_name = kubernetes_storage_class.nfs.metadata[0].name
    access_modes       = ["ReadWriteMany"]
    persistent_volume_source {
      nfs {
        path   = "/vol1"
        server = data.terraform_remote_state.gke.outputs.google_filestore_reserved_ip_range
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim_v1" "nfs_pvc" {
  metadata {
    name = "vol1"
  }
  spec {
    access_modes       = ["ReadWriteMany"]
    storage_class_name = kubernetes_storage_class.nfs.metadata[0].name
    volume_name        = kubernetes_persistent_volume_v1.nfs_pv.metadata.0.name
    resources {
      requests = {
        storage = "1Ti"
      }
    }
  }
}

resource "null_resource" "connect_regional_cluster" {
  count = data.terraform_remote_state.gke.outputs.cluster_type == "regional" ? 1 : 0
  provisioner "local-exec" {
    command = "gcloud container clusters get-credentials ${data.terraform_remote_state.gke.outputs.kubernetes_cluster_name} --region ${data.terraform_remote_state.gke.outputs.gke_location} --project ${data.terraform_remote_state.gke.outputs.project_id}"
  }
}
resource "null_resource" "connect_zonal_cluster" {
  count = data.terraform_remote_state.gke.outputs.cluster_type == "zonal" ? 1 : 0
  provisioner "local-exec" {
    command = "gcloud container clusters get-credentials ${data.terraform_remote_state.gke.outputs.kubernetes_cluster_name}  --zone ${data.terraform_remote_state.gke.outputs.gke_location} --project ${data.terraform_remote_state.gke.outputs.project_id}"
  }
}

resource "null_resource" "node_gpu_driver" {
  provisioner "local-exec" {
    command = "kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml"
  }
}

resource "null_resource" "sample_sd15_deployment" {
  provisioner "local-exec" {
    command = "kubectl apply -f deployment_sd15.yaml"
  }
}