terraform {
  required_providers {
    null = {
      source  = "hashicorp/null"
      version = "3.2.1"
    }
  }
}
resource "null_resource" "build_webui_image" {
  provisioner "local-exec" {
    command     = "gcloud builds submit --machine-type=e2-highcpu-32 --disk-size=100 --region=us-central1 -t ${var.artifact_registry}/${var.sd_webui_image.tag}"
    working_dir = var.sd_webui_image.path
  }
}
resource "null_resource" "build_game_server_image" {
  provisioner "local-exec" {
    command     = "gcloud builds submit --machine-type=e2-highcpu-32 --disk-size=100 --region=us-central1 -t ${var.artifact_registry}/${var.game_server_image.tag}"
    working_dir = var.game_server_image.path
  }
}
resource "null_resource" "modify_nginx_image" {
  provisioner "local-exec" {
    command     = "sed -i 's/$${REDIS_HOST}/redis.private.domain/g' sd.lua"
    working_dir = var.nginx_image.path
  }
}

resource "null_resource" "build_nginx_image" {
  provisioner "local-exec" {
    command     = "gcloud builds submit --machine-type=e2-highcpu-32 --disk-size=100 --region=us-central1 -t ${var.artifact_registry}/${var.nginx_image.tag}"
    working_dir = var.nginx_image.path
  }
}