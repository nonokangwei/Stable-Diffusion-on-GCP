variable "sd_webui_image" {
  description = "Region to set for gcp resource deploy."
  type = object({
    path = string
    tag  = string
  })
  default = {
    path = "../Stable-Diffusion-UI-GKE/docker/"
    tag  = "sd-webui:tf"
  }
}
variable "artifact_registry" {
  type        = string
  description = "artifact registry URL."
}