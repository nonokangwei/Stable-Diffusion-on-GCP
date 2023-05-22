output "cluster_type" {
  value       = var.cluster_location == var.region ? "regional" : "zonal"
  description = "GCloud Region"
}
output "region" {
  value       = var.region
  description = "GCloud Region"
}
output "gke_location" {
  value       = var.cluster_location
  description = "gke location"
}
output "project_id" {
  value       = var.project_id
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
  value       = "gcloud auth configure-docker ${var.region}-docker.pkg.dev"
  description = "repositories login gcloud example"
}
output "cloud_build_image_cmd_sample" {
  value       = "gcloud builds submit --machine-type=e2-highcpu-32 --disk-size=100 --region=${var.region} -t ${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.sd_repo.name}/sd-webui:TAG"
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
output "artifactregistry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.sd_repo.name}"
  description = "artifactregistry_url"
}