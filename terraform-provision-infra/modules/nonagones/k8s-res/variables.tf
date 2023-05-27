variable "gke_cluster_name" {
  description = "GKE Cluster Name."
  type        = string
}
variable "gke_cluster_location" {
  description = "GKE Cluster Location"
  type        = string
}
variable "project_id" {
  description = "GCP project id"
  type        = string
}
variable "google_filestore_reserved_ip_range" {
  description = "GCP project id"
  type        = string
}
variable "gke_cluster_nodepool" {
  description = "GCP project id"
  type        = string
}
variable "webui_image_url" {
  description = "Stable diffusion webui Image url"
  type        = string
}