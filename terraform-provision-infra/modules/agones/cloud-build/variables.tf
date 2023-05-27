variable "nginx_image" {
  description = "Region to set for gcp resource deploy."
  type = object({
    path = string
    tag  = string
  })
  default = {
    path = "../Stable-Diffusion-UI-Agones/nginx/"
    tag  = "nginx:tf"
  }
}
variable "sd_webui_image" {
  description = "Region to set for gcp resource deploy."
  type = object({
    path = string
    tag  = string
  })
  default = {
    path = "../Stable-Diffusion-UI-Agones/sd-webui/"
    tag  = "sd-webui:tf"
  }
}
variable "game_server_image" {
  description = "Region to set for gcp resource deploy."
  type = object({
    path = string
    tag  = string
  })
  default = {
    path = "../Stable-Diffusion-UI-Agones/agones-sidecar/"
    tag  = "game-server:tf"
  }
}
variable "artifact_registry" {
  type        = string
  description = "artifact registry URL."
}