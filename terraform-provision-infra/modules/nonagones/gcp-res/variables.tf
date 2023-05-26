# Input variable definitions
variable "project_id" {
  description = "Project ID of the cloud resource."
  type        = string
}

variable "region" {
  description = "Region to set for gcp resource deploy."
  type        = string
}
variable "filestore_zone" {
  description = "Zone to set for filestore nfs server, should be same zone with gke node."
  type        = string
}

variable "cluster_location" {
  description = "gke cluster location choose a zone or region."
  type        = string
}
variable "node_machine_type" {
  description = "gke node machine type."
  type        = string
  default     = "custom-12-49152-ext"
}

variable "accelerator_type" {
  description = "Get available accelerator_type from gcloud compute accelerator-types list --format='csv(zone,name)' "
  type        = string
  default     = "nvidia-tesla-t4"
}
variable "gke_num_nodes" {
  description = "Tags to set on the bucket."
  type        = number
  default     = 1
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
    "networkmanagement.googleapis.com"
  ]
}

