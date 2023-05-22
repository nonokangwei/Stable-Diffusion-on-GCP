output "webui_image" {
  value       = "${var.artifact_registry}/${var.sd_webui_image.tag}"
  description = "webui image url"
}
output "nginx_image" {
  value       = "${var.artifact_registry}/${var.nginx_image.tag}"
  description = "nginx image url"
}
output "game_server_image" {
  value       = "${var.artifact_registry}/${var.nginx_image.tag}"
  description = "nginx image url"
}