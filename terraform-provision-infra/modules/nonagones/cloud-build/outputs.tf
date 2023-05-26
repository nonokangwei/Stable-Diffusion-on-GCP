output "webui_image" {
  value       = "${var.artifact_registry}/${var.sd_webui_image.tag}"
  description = "webui image url"
}