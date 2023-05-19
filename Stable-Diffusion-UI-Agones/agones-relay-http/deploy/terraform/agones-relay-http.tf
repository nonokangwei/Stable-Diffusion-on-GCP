resource kubernetes_deployment "agones-relay-http" {
  metadata {
    name = var.service_name
    namespace = var.namespace
    labels = {
      name = var.service_name 
      app  = var.service_name
    }
  }

  spec {
    replicas = 1
    selector {
      match_labels = {
        app = var.service_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.service_name
        }
      }
      spec {
        service_account_name = kubernetes_service_account.agones-relay-http-sa.metadata[0].name
        # below is an example, you may remove if you don't care where the service runs
        node_selector = {
          role = "services"
        }
        container {
          image = "octops/agones-relay-http:${var.agones_relay_image_version}"
          name  = "relay-http"
          args = [
              "--sync-period=15s",
              "--on-event-url=http://www.myendpoint.com/webhook",
              "--verbose"
              #"--on-add-url=http://www.myendpoint.com/onadd",
              #"--on-update-url=http://www.myendpoint.com/onupdate",
              #"--on-delete-url=http://www.myendpoint.com/ondelete",
          ]
          image_pull_policy = "IfNotPresent"
          resources {
            limits = {
              cpu    = "0.1"
              memory = "50Mi"
            }
            requests = {
              cpu    = "1"
              memory = "100Mi"
            }
          }  
        }
      }
    }
  }
}

resource "kubernetes_service_account" "agones-relay-http-sa" {
metadata {
    name = var.service_name
    labels = {
        app = var.service_name
    }
    namespace = var.namespace
  }
}

resource "kubernetes_cluster_role" "agones-relay-http-cr" {
  metadata {
    name = var.service_name
    labels = {
        app = var.service_name
    }
  }
  rule {
    api_groups     = [""]
    resources      = ["pods"]
    verbs          = ["list", "watch"]
  }
  rule {
    api_groups     = ["agones.dev"]
    resources      = ["gameservers", "fleets"]
    verbs          = ["get", "list", "watch"]
  }
}

resource "kubernetes_cluster_role_binding" "agones-relay-http-crb" {
  metadata {
    name = var.service_name
    labels = {
        app = var.service_name
    }
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.agones-relay-http-cr.metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.agones-relay-http-sa.metadata[0].name
    namespace = var.namespace
  }
}
