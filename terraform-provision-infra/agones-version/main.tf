terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "4.63.1"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.5.1"
    }
  }
}
locals {
  project_id       = "PROJECT_ID"
  region           = "us-central1"
  filestore_zone   = "us-central1-f"   # Filestore location must be same region or zone with gke
  cluster_location = "us-central1-f"   # GKE Cluster location
  accelerator_type = "nvidia-tesla-t4" # Available accelerator_type from gcloud compute accelerator-types list --format='csv(zone,name)'
  gke_num_nodes    = 1
}

provider "google" {
  project = local.project_id
  region  = local.region
}
resource "random_id" "tf_subfix" {
  byte_length = 4
}

variable "gcp_service_list" {
  description = "The list of apis necessary for the project"
  type        = list(string)
  default = [
    "artifactregistry.googleapis.com",
    "cloudbuild.googleapis.com",
    "compute.googleapis.com",
    "container.googleapis.com",
    "file.googleapis.com",
    "networkmanagement.googleapis.com",
    "memcache.googleapis.com",
    "cloudfunctions.googleapis.com",
    "cloudscheduler.googleapis.com",
    "iap.googleapis.com",
    "dns.googleapis.com",
    "redis.googleapis.com",
    "vpcaccess.googleapis.com"
  ]
}

# Enable related service
resource "google_project_service" "gcp_services" {
  for_each                   = toset(var.gcp_service_list)
  project                    = local.project_id
  service                    = each.key
  disable_dependent_services = false
  disable_on_destroy         = false
}

data "google_compute_default_service_account" "default" {
  depends_on = [google_project_service.gcp_services]
}

# VPC
resource "google_compute_network" "vpc" {
  project                 = local.project_id
  name                    = "tf-gen-vpc-${random_id.tf_subfix.hex}"
  auto_create_subnetworks = "false"
  depends_on              = [google_project_service.gcp_services]
}

# Subnet
resource "google_compute_subnetwork" "subnet" {
  name          = "tf-gen-subnet-${random_id.tf_subfix.hex}"
  region        = local.region
  network       = google_compute_network.vpc.name
  ip_cidr_range = "10.10.0.0/16"
}

# Cloud Router
resource "google_compute_router" "router" {
  name    = "tf-gen-router-${local.region}-${random_id.tf_subfix.hex}"
  region  = google_compute_subnetwork.subnet.region
  network = google_compute_network.vpc.id
}
# NAT IP
resource "google_compute_address" "address" {
  count      = 2
  name       = "nat-manual-ip-${count.index}"
  region     = google_compute_subnetwork.subnet.region
  depends_on = [google_project_service.gcp_services]
}

resource "google_compute_global_address" "webui_addr" {
  name       = "sd-webui-ingress-${random_id.tf_subfix.hex}"
  depends_on = [google_project_service.gcp_services]
}

# NAT Gateway
resource "google_compute_router_nat" "nat" {
  name                               = "tf-gen-${local.region}-nat-gw"
  router                             = google_compute_router.router.name
  region                             = google_compute_router.router.region
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = google_compute_address.address.*.self_link
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"
}

# GKE cluster
resource "google_container_cluster" "gke" {
  name                     = "tf-gen-gke-${random_id.tf_subfix.hex}"
  location                 = local.cluster_location
  remove_default_node_pool = true
  enable_shielded_nodes    = true
  initial_node_count       = 1
  network                  = google_compute_network.vpc.name
  subnetwork               = google_compute_subnetwork.subnet.name
  private_cluster_config {
    enable_private_nodes    = true
    master_ipv4_cidr_block  = "192.168.1.0/28"
  }
  ip_allocation_policy {
  }
  monitoring_config {
    enable_components = ["SYSTEM_COMPONENTS", "APISERVER", "SCHEDULER", "CONTROLLER_MANAGER"]
    managed_prometheus { enabled = true }
  }
  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS", "APISERVER", "SCHEDULER", "CONTROLLER_MANAGER"]
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
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = false
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
  node_config {
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
  #   lifecycle {
  #     ignore_changes = all
  #   }
}

# Separately Managed Node Pool
resource "google_container_node_pool" "gpu_nodepool" {
  name     = "${local.accelerator_type}-nodepool"
  location = local.cluster_location
  cluster  = google_container_cluster.gke.name
  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }
  #   lifecycle {
  #     ignore_changes = all
  #   }
  node_count = local.gke_num_nodes
  node_config {
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]

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
      type  = local.accelerator_type
      count = 1
      gpu_sharing_config {
        gpu_sharing_strategy       = "TIME_SHARING"
        max_shared_clients_per_gpu = 2
      }
    }
    disk_type    = "pd-balanced"
    disk_size_gb = 100

    tags = ["gpu-node", "gke-sd"]
    metadata = {
      disable-legacy-endpoints = "true"
    }
    shielded_instance_config {
      enable_secure_boot          = true
      enable_integrity_monitoring = true
    }
  }
}
#agones firewall
resource "google_compute_firewall" "agones" {
  depends_on = [google_container_cluster.gke]
  name       = "allow-agones-${random_id.tf_subfix.hex}"
  network    = google_compute_network.vpc.name
  project    = local.project_id
  allow {
    protocol = "tcp"
    ports    = ["443", "8080", "8081"]
  }
  source_ranges = ["0.0.0.0/0"]
}
# Filestore
resource "google_filestore_instance" "instance" {
  name     = "nfs-store-${random_id.tf_subfix.hex}"
  location = local.filestore_zone
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
#Artifact Registry
resource "google_artifact_registry_repository" "sd_repo" {
  location      = local.region
  repository_id = "sd-repository-${random_id.tf_subfix.hex}"
  description   = "stable diffusion repository"
  format        = "DOCKER"
  depends_on    = [google_project_service.gcp_services]
}
# Redis cache
resource "google_redis_instance" "cache" {
  region             = local.region
  name               = "sd-agones-cache-${random_id.tf_subfix.hex}"
  tier               = "BASIC"
  memory_size_gb     = 1
  authorized_network = google_compute_network.vpc.id
  redis_version      = "REDIS_6_X"
  display_name       = "Stable Diffusion Agones Cache Instance"
  connect_mode       = "DIRECT_PEERING"
  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 0
        minutes = 30
        seconds = 0
        nanos   = 0
      }
    }
  }
}

resource "google_vpc_access_connector" "connector" {
  name          = "vpc-con-${random_id.tf_subfix.hex}"
  ip_cidr_range = "192.168.240.16/28"
  network       = google_compute_network.vpc.name
}

resource "google_storage_bucket" "bucket" {
  name                        = "cloud-function-source-${random_id.tf_subfix.hex}"
  project                     = local.project_id
  location                    = local.region
  force_destroy               = true
  storage_class               = "COLDLINE"
  uniform_bucket_level_access = true
  depends_on                  = [google_project_service.gcp_services]
}

resource "google_storage_bucket_object" "archive" {
  name   = "function.zip"
  bucket = google_storage_bucket.bucket.id
  source = "function.zip"
}

resource "google_cloudfunctions_function" "function" {
  name                          = "redis-http-${random_id.tf_subfix.hex}"
  description                   = "agones gpu pod recycle function"
  runtime                       = "python310"
  trigger_http                  = true
  region                        = local.region
  ingress_settings              = "ALLOW_INTERNAL_AND_GCLB"
  vpc_connector                 = google_vpc_access_connector.connector.name
  vpc_connector_egress_settings = "PRIVATE_RANGES_ONLY"
  entry_point                   = "redis_http"
  environment_variables = {
    REDIS_HOST = google_redis_instance.cache.host
  }
  available_memory_mb   = 128
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.archive.name
  timeout               = 60
  depends_on            = [google_storage_bucket_object.archive]
}

resource "google_cloudfunctions_function_iam_member" "invoker" {
  project        = google_cloudfunctions_function.function.project
  region         = google_cloudfunctions_function.function.region
  cloud_function = google_cloudfunctions_function.function.name

  role       = "roles/cloudfunctions.invoker"
  member     = "serviceAccount:${data.google_compute_default_service_account.default.email}"
  depends_on = [google_project_service.gcp_services]
}

resource "google_cloud_scheduler_job" "job" {
  name        = "sd-agones-cruiser-${random_id.tf_subfix.hex}"
  description = "cloud function http schedule job"
  region      = local.region
  schedule    = "*/5 * * * *"
  http_target {
    http_method = "GET"
    uri         = google_cloudfunctions_function.function.https_trigger_url
    oidc_token {
      service_account_email = data.google_compute_default_service_account.default.email
    }
  }
  depends_on = [google_project_service.gcp_services]
}

resource "google_dns_managed_zone" "private_zone" {
  name        = "private-zone-${random_id.tf_subfix.hex}"
  dns_name    = "private.domain."
  description = "Example private DNS zone"
  visibility  = "private"
  private_visibility_config {
    networks {
      network_url = google_compute_network.vpc.id
    }
  }
  depends_on = [google_project_service.gcp_services]
}

resource "google_dns_record_set" "redis_a" {
  name         = "redis.${google_dns_managed_zone.private_zone.dns_name}"
  managed_zone = google_dns_managed_zone.private_zone.name
  type         = "A"
  ttl          = 300
  rrdatas      = [google_redis_instance.cache.host]
}

output "cluster_type" {
  value       = local.cluster_location == local.region ? "regional" : "zonal"
  description = "GCloud Region"
}
output "region" {
  value       = local.region
  description = "GCloud Region"
}
output "gke_location" {
  value       = local.cluster_location
  description = "gke location"
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
output "gcloud_artifacts_repositories_auth_cmd" {
  value       = "gcloud auth configure-docker ${local.region}-docker.pkg.dev"
  description = "repositories login gcloud example"
}
output "cloud_build_image_cmd_sample" {
  value       = "gcloud builds submit --machine-type=e2-highcpu-32 --disk-size=100 --region=${local.region} -t ${local.region}-docker.pkg.dev/${local.project_id}/${google_artifact_registry_repository.sd_repo.name}/sd-webui:TAG"
  description = "cloud build sample command"
}
output "google_redis_instance_host" {
  value       = google_redis_instance.cache.host
  description = "redis host"
}
output "gcs_function_archive_bucket" {
  value       = google_storage_bucket.bucket.name
  description = "cloud function source archive bucket"
}
output "gcs_function_archive_object" {
  value       = google_storage_bucket_object.archive.name
  description = "cloud function source archive object name"
}
output "webui_address_name" {
  value       = google_compute_global_address.webui_addr.name
  description = "webui global static ip name"
}
output "webui_address" {
  value       = google_compute_global_address.webui_addr.address
  description = "webui global static ip address"
}
output "redis_private_domain" {
  value       = google_dns_record_set.redis_a.name
  description = "redis private domain"
}
output "gpu_nodepool_name" {
  value       = google_container_node_pool.gpu_nodepool.name
  description = "gpu node pool name"
}