output "kubernetes_cluster_name" {
  value       = google_container_cluster.gke.name
  description = "GKE Cluster Name"
}
output "google_filestore_reserved_ip_range" {
  value       = google_filestore_instance.instance.networks[0].ip_addresses[0]
  description = "google_filestore_instance reserved_ip_range"
}
output "gpu_nodepool_name" {
  value       = google_container_node_pool.separately_gpu_nodepool.name
  description = "gpu node pool name"
}
output "artifactregistry_url" {
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.sd_repo.name}"
  description = "artifactregistry_url"
}