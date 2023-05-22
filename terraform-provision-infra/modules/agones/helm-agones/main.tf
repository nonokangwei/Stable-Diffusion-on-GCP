terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.63.1"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "2.9.0"
    }
  }
}
data "google_client_config" "default" {}

data "google_container_cluster" "my_cluster" {
  name     = var.gke_cluster_name
  location = var.gke_cluster_location
  project  = var.project_id
}

provider "kubernetes" {
  host  = "https://${data.google_container_cluster.my_cluster.endpoint}"
  token = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(
    data.google_container_cluster.my_cluster.master_auth[0].cluster_ca_certificate,
  )
  experiments {
    manifest_resource = true
  }
}

provider "helm" {
  kubernetes {
    host  = "https://${data.google_container_cluster.my_cluster.endpoint}"
    token = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(
      data.google_container_cluster.my_cluster.master_auth[0].cluster_ca_certificate,
    )
  }
}

resource "helm_release" "agones" {
  name             = "agones"
  repository       = "https://agones.dev/chart/stable"
  chart            = "agones"
  namespace        = "agones-system"
  create_namespace = true
  values = [
    file("../Stable-Diffusion-UI-Agones/agones/values.yaml")
  ]
  set {
    name  = "agones.controller.nodeSelector.cloud\\.google\\.com/gke-nodepool"
    value = var.gke_cluster_nodepool
    type  = "string"
  }
  set {
    name  = "agones.ping.nodeSelector.cloud\\.google\\.com/gke-nodepool"
    value = var.gke_cluster_nodepool
    type  = "string"
  }
  set {
    name  = "agones.allocator.nodeSelector.cloud\\.google\\.com/gke-nodepool"
    value = var.gke_cluster_nodepool
    type  = "string"
  }
}