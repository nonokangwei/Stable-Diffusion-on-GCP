terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.60.1"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.19.0"
    }
  }
}
locals {
  project_id    = "star-ai-poc"
  region        = "us-central1"
  zone          = "us-central1-f"
  gke_num_nodes = 1
}
provider "google" {
  project = local.project_id
  region  = local.region
}

# VPC
resource "google_compute_network" "vpc" {
  project                 = local.project_id
  name                    = "tf-generate-vpc-${local.project_id}"
  auto_create_subnetworks = "false"
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "${local.region}-subnet"
  region        = local.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.10.0.0/16"
}

# Cloud Router
resource "google_compute_router" "router" {
  name    = "tf-generate-router-${local.region}"
  region  = google_compute_subnetwork.subnet.region
  network = google_compute_network.vpc.id
}
# NAT IP
resource "google_compute_address" "address" {
  count  = 2
  name   = "nat-manual-ip-${count.index}"
  region = google_compute_subnetwork.subnet.region
}

# NAT
resource "google_compute_router_nat" "nat" {
  name   = "tf-generate-${local.region}-nat-gw"
  router = google_compute_router.router.name
  region = google_compute_router.router.region

  nat_ip_allocate_option = "MANUAL_ONLY"
  nat_ips                = google_compute_address.address.*.self_link

  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  subnetwork {
    name                    = google_compute_subnetwork.subnet.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
}

# GKE cluster
resource "google_container_cluster" "gke" {
  name                     = "tf-gke-${local.region}"
  location                 = local.region
  remove_default_node_pool = true
  initial_node_count       = 1
  network                  = google_compute_network.vpc.name
  subnetwork               = google_compute_subnetwork.subnet.name
  private_cluster_config {
    enable_private_nodes   = "true"
    master_ipv4_cidr_block = "192.168.1.0/28"
  }
  ip_allocation_policy {
  }
  monitoring_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "APISERVER",
      "SCHEDULER",
    "CONTROLLER_MANAGER"]
    managed_prometheus { enabled = true }
  }
  logging_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "WORKLOADS",
      "APISERVER",
      "SCHEDULER",
    "CONTROLLER_MANAGER"]
  }

  release_channel {
    channel = "STABLE"
  }
  maintenance_policy {
    daily_maintenance_window {
      start_time = "03:00"
    }
  }
  addons_config {
    http_load_balancing {
      disabled = true
    }

    horizontal_pod_autoscaling {
      disabled = true
    }

    gcp_filestore_csi_driver_config {
      enabled = true
    }

    gce_persistent_disk_csi_driver_config {
      enabled = true
    }

    dns_cache_config {
      enabled = true
    }
  }
}

# Separately Managed Node Pool
resource "google_container_node_pool" "gpu_nodes" {
  name     = "auto-scaling-gpu-pool"
  location = local.region
  cluster  = google_container_cluster.gke.name
  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }
  node_count = local.gke_num_nodes
  node_config {
    oauth_scopes = [
      #      "https://www.googleapis.com/auth/logging.write",
      #      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/cloud-platform"
    ]
    #    service_account = "gke-svc-acct@star-ai-poc.iam.gserviceaccount.com"

    labels = {
      env = local.project_id
    }

    preemptible  = true
    machine_type = "custom-12-49152-ext"
    image_type   = "COS_CONTAINERD"
    gcfs_config {
      enabled = true
    }
    guest_accelerator {
      type  = "nvidia-tesla-t4"
      count = 1
      gpu_sharing_config {
        gpu_sharing_strategy       = "TIME_SHARING"
        max_shared_clients_per_gpu = 2

      }
    }
    disk_type    = "pd-balanced"
    disk_size_gb = 100

    tags = [
      "gke-node",
    "${local.project_id}-gke"]
    metadata = {
      disable-legacy-endpoints = "true"
    }
  }
}
#gcloud filestore instances create nfs-store --zone=us-central1-b --tier=BASIC_HDD
#--file-share=name="vol1",capacity=1TB --network=name=${VPC_NETWORK}
resource "google_filestore_instance" "instance" {
  name     = "nfs-store"
  location = "us-central1-b"
  tier     = "BASIC_HDD"

  file_shares {
    capacity_gb = 1024
    name        = "vol1"
  }

  networks {
    network = google_compute_network.vpc.name
    modes   = ["MODE_IPV4"]
  }
}
resource "google_artifact_registry_repository" "sd_repo" {
  location      = local.region
  repository_id = "sd-repository"
  description   = "stable diffusion repository"
  format        = "DOCKER"
}
output "region" {
  value       = local.region
  description = "GCloud Region"
}

output "project_id" {
  value       = local.project_id
  description = "GCloud Project ID"
}

output "kubernetes_cluster_name" {
  value       = google_container_cluster.gke.name
  description = "GKE Cluster Name"
}

output "kubernetes_cluster_host" {
  value       = google_container_cluster.gke.endpoint
  description = "GKE Cluster Host"
}
output "google_filestore_reserved_ip_range" {
  value       = google_filestore_instance.instance.networks[0].ip_addresses[0]
  description = "google_filestore_instance reserved_ip_range"
}
#gcloud auth configure-docker ${REGION}-docker.pkg.dev
output "gcloud_artifacts_repositories_auth_cmd" {
  value       = "gcloud auth configure-docker ${local.region}-docker.pkg.dev"
  description = "repositories login gcloud example"
}
