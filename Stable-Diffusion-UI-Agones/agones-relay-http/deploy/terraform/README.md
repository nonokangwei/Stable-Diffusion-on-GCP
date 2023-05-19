# How to use this Terraform config

You will need a valid `kubeconfig` to point to in the `provider.tf` file, and sufficient permissions to deploy this to your cluster. This version is based off the `install.yaml` file at the time of writing and would need to be updated in lock step to reflect any changes there.

Once you have a valid config to point it at for the `kubernetes` provider, and assuming you are OK with the `default` namespace and other config options, you can deploy using the standard Terraform `plan/apply` commands. For reference, below is an extract of a plan output prior to an apply to give an idea of the changes that will be made:

```bash
$ terraform plan
...
Terraform will perform the following actions:

  # agones-relay-http.kubernetes_cluster_role.agones-relay-http-cr will be created
  + resource "kubernetes_cluster_role" "agones-relay-http-cr" {
      + id = (known after apply)

      + metadata {
          + generation       = (known after apply)
          + labels           = {
              + "app" = "agones-relay-http"
            }
          + name             = "agones-relay-http"
          + resource_version = (known after apply)
          + self_link        = (known after apply)
          + uid              = (known after apply)
        }

      + rule {
          + api_groups = [
              + "",
            ]
          + resources  = [
              + "pods",
            ]
          + verbs      = [
              + "list",
              + "watch",
            ]
        }
      + rule {
          + api_groups = [
              + "agones.dev",
            ]
          + resources  = [
              + "gameservers",
              + "fleets",
            ]
          + verbs      = [
              + "get",
              + "list",
              + "watch",
            ]
        }
    }

  # agones-relay-http.kubernetes_cluster_role_binding.agones-relay-http-crb will be created
  + resource "kubernetes_cluster_role_binding" "agones-relay-http-crb" {
      + id = (known after apply)

      + metadata {
          + generation       = (known after apply)
          + labels           = {
              + "app" = "agones-relay-http"
            }
          + name             = "agones-relay-http"
          + resource_version = (known after apply)
          + self_link        = (known after apply)
          + uid              = (known after apply)
        }

      + role_ref {
          + api_group = "rbac.authorization.k8s.io"
          + kind      = "ClusterRole"
          + name      = "agones-relay-http"
        }

      + subject {
          + api_group = (known after apply)
          + kind      = "ServiceAccount"
          + name      = "agones-relay-http"
          + namespace = "default"
        }
    }

  # agones-relay-http.kubernetes_deployment.agones-relay-http will be created
  + resource "kubernetes_deployment" "agones-relay-http" {
      + id               = (known after apply)
      + wait_for_rollout = true

      + metadata {
          + generation       = (known after apply)
          + labels           = {
              + "app"  = "agones-relay-http"
              + "name" = "agones-relay-http"
            }
          + name             = "agones-relay-http"
          + namespace        = "default"
          + resource_version = (known after apply)
          + self_link        = (known after apply)
          + uid              = (known after apply)
        }

      + spec {
          + min_ready_seconds         = 0
          + paused                    = false
          + progress_deadline_seconds = 600
          + replicas                  = "1"
          + revision_history_limit    = 10

          + selector {
              + match_labels = {
                  + "app" = "agones-relay-http"
                }
            }

          + strategy {
              + type = (known after apply)

              + rolling_update {
                  + max_surge       = (known after apply)
                  + max_unavailable = (known after apply)
                }
            }

          + template {
              + metadata {
                  + generation       = (known after apply)
                  + labels           = {
                      + "app" = "agones-relay-http"
                    }
                  + name             = (known after apply)
                  + resource_version = (known after apply)
                  + self_link        = (known after apply)
                  + uid              = (known after apply)
                }

              + spec {
                  + automount_service_account_token  = true
                  + dns_policy                       = "ClusterFirst"
                  + enable_service_links             = true
                  + host_ipc                         = false
                  + host_network                     = false
                  + host_pid                         = false
                  + hostname                         = (known after apply)
                  + node_name                        = (known after apply)
                  + node_selector                    = {
                      + "role" = "services"
                    }
                  + restart_policy                   = "Always"
                  + service_account_name             = "agones-relay-http"
                  + share_process_namespace          = false
                  + termination_grace_period_seconds = 30

                  + container {
                      + args                       = [
                          + "--sync-period=15s",
                          + "--on-event-url=http://www.myendpoint.com/webhook",
                          + "--verbose",
                        ]
                      + image                      = "octops/agones-relay-http:0.1.0"
                      + image_pull_policy          = "IfNotPresent"
                      + name                       = "relay-http"
                      + stdin                      = false
                      + stdin_once                 = false
                      + termination_message_path   = "/dev/termination-log"
                      + termination_message_policy = (known after apply)
                      + tty                        = false

                      + resources {
                          + limits   = {
                              + "cpu"    = "0.1"
                              + "memory" = "50Mi"
                            }
                          + requests = {
                              + "cpu"    = "1"
                              + "memory" = "100Mi"
                            }
                        }

                }
            }
        }
    }

  # agones-relay-http.kubernetes_service_account.agones-relay-http-sa will be created
  + resource "kubernetes_service_account" "agones-relay-http-sa" {
      + automount_service_account_token = true
      + default_secret_name             = (known after apply)
      + id                              = (known after apply)

      + metadata {
          + generation       = (known after apply)
          + labels           = {
              + "app" = "agones-relay-http"
            }
          + name             = "agones-relay-http"
          + namespace        = "default"
          + resource_version = (known after apply)
          + self_link        = (known after apply)
          + uid              = (known after apply)
        }
    }

```

There are variables for the name and the namespace that it deploys to. These are just to make it more convenient to change them if you wish. The arguments being in a variable would allow you to (for example) have them as an easily editable variable in Terraform Cloud/Enterprise and change them without making any changes to the Terraform code itself. Similarly the version tag of the container image has been made a variable to make updates easier to deploy without altering the code itself.