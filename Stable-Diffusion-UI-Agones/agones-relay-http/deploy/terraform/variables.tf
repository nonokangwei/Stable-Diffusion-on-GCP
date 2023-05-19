variable "service_name" {
  default = "agones-relay-http"
}
variable "namespace" {
  default = "default"
}
variable "agones_relay_arguments" {
  default = [
    "--sync-period=15s",
    "--on-event-url=http://www.myendpoint.com/webhook",
    "--verbose"
    #"--on-add-url=http://www.myendpoint.com/onadd",
    #"--on-update-url=http://www.myendpoint.com/onupdate",
    #"--on-delete-url=http://www.myendpoint.com/ondelete",
  ]
}
variable "agones_relay_image_version" {
  default = "0.1.0"
}