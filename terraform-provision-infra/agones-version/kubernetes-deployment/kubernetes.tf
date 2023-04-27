
data "terraform_remote_state" "gke" {
  backend = "local"

  config = {
    path = "../terraform.tfstate"
  }
}

locals {
  oauth_client_id  = "OAUTH_CLIENT_ID"
  oauth_client_secret = "OAUTH_CLIENT_SECRET"
  sd_webui_domain = "your_owned_domain_or_subdomain"
}

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

provider "helm" {
  kubernetes {
    host                   = "https://${data.terraform_remote_state.gke.outputs.kubernetes_cluster_host}"
    token                  = data.google_client_config.default.access_token
    cluster_ca_certificate = base64decode(data.google_container_cluster.my_cluster.master_auth[0].cluster_ca_certificate)
  }
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

resource "kubernetes_secret" "iap_client_secret" {
  metadata {
    name = "iap-secret"
  }
  data = {
    client_id     = local.oauth_client_id
    client_secret = local.oauth_client_secret
  }
}
resource "kubernetes_namespace" "agones_namespace" {
  metadata {
    name = "agones-system"
  }
}

resource "helm_release" "agones" {
  name       = "agones"
  repository = "https://agones.dev/chart/stable"
  chart      = "agones"
  namespace  = kubernetes_namespace.agones_namespace.metadata[0].name

  values = [
    file("./agones-values.yaml")
  ]
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
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -f https://raw.githubusercontent.com/GoogleCloudPlatform/container-engine-accelerators/master/nvidia-driver-installer/cos/daemonset-preloaded.yaml"
  }
  depends_on = [null_resource.connect_zonal_cluster, null_resource.connect_regional_cluster]
}

resource "null_resource" "custom_metrics_stackdriver_adapter" {
  provisioner "local-exec" {
    command = "kubectl apply -f https://raw.githubusercontent.com/GoogleCloudPlatform/k8s-stackdriver/master/custom-metrics-stackdriver-adapter/deploy/production/adapter_new_resource_model.yaml"
  }
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -f https://raw.githubusercontent.com/GoogleCloudPlatform/k8s-stackdriver/master/custom-metrics-stackdriver-adapter/deploy/production/adapter_new_resource_model.yaml"
  }
  depends_on = [null_resource.connect_zonal_cluster, null_resource.connect_regional_cluster]
}

resource "null_resource" "sample_nginx_deployment" {
  provisioner "local-exec" {
    command = "kubectl apply -f nginx-deployment.yaml"
  }
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -f nginx-deployment.yaml"
  }
  depends_on = [null_resource.connect_zonal_cluster, null_resource.connect_regional_cluster]
}

resource "null_resource" "sample_fleet" {
  provisioner "local-exec" {
    command = "kubectl apply -f fleet.yaml"
  }
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -f fleet.yaml"
  }
  depends_on = [null_resource.connect_zonal_cluster, null_resource.connect_regional_cluster]
}

resource "null_resource" "sample_fleet__autoscaler" {
  provisioner "local-exec" {
    command = "kubectl apply -f fleet-autoscaler.yaml"
  }
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -f fleet-autoscaler.yaml"
  }
  depends_on = [null_resource.connect_zonal_cluster, null_resource.connect_regional_cluster, null_resource.sample_fleet]
}

resource "null_resource" "sample_iap_ingress" {
  provisioner "local-exec" {
    command = "export DOMAIN=${local.sd_webui_domain} && export IP_NAME=${data.terraform_remote_state.gke.outputs.webui_address_name} && envsubst <  iap-ingress.yaml | kubectl apply -f -"
  }
  provisioner "local-exec" {
    when    = destroy
    command = "kubectl delete -f iap-ingress.yaml"
  }
  depends_on = [null_resource.connect_zonal_cluster, null_resource.connect_regional_cluster]
}