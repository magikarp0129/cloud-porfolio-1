resource "kubernetes_manifest" "vpc_cni_eni_config" {
  for_each = var.vpc_cni_eni_configs

  manifest = {
    apiVersion = "crd.k8s.amazonaws.com/v1alpha1"
    kind       = "ENIConfig"
    metadata = {
      name = each.key
    }
    spec = {
      subnet         = each.value.subnet_id
      securityGroups = sort(tolist(each.value.security_group_ids))
    }
  }
}

resource "kubernetes_namespace_v1" "istio_system" {
  metadata {
    name = "istio-system"

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  depends_on = [kubernetes_manifest.vpc_cni_eni_config]
}

resource "helm_release" "istio_base" {
  name       = "istio-base"
  namespace  = kubernetes_namespace_v1.istio_system.metadata[0].name
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "base"
  version    = var.istio_version
  atomic     = true
  timeout    = 600
}

resource "helm_release" "istiod" {
  name       = "istiod-${var.istio_revision}"
  namespace  = kubernetes_namespace_v1.istio_system.metadata[0].name
  repository = "https://istio-release.storage.googleapis.com/charts"
  chart      = "istiod"
  version    = var.istio_version
  atomic     = true
  timeout    = 600

  values = [yamlencode({
    revision = var.istio_revision
    global = {
      proxy = {
        holdApplicationUntilProxyStarts = true
      }
    }
    meshConfig = {
      accessLogFile = "/dev/stdout"
      enableTracing = true
    }
    pilot = {
      autoscaleEnabled = true
      autoscaleMin     = 2
      autoscaleMax     = 5
    }
  })]

  depends_on = [helm_release.istio_base]
}

resource "helm_release" "istio_ingress" {
  count = var.enable_istio_ingress ? 1 : 0

  name             = "istio-ingress"
  namespace        = "istio-ingress"
  create_namespace = true
  repository       = "https://istio-release.storage.googleapis.com/charts"
  chart            = "gateway"
  version          = var.istio_version
  atomic           = true
  timeout          = 600

  values = [yamlencode({
    labels = {
      "istio.io/rev" = var.istio_revision
    }
    service = {
      type = "LoadBalancer"
      annotations = {
        "service.beta.kubernetes.io/aws-load-balancer-scheme" = "internal"
        "service.beta.kubernetes.io/aws-load-balancer-type"   = "external"
      }
    }
  })]

  depends_on = [helm_release.istiod]
}

resource "kubernetes_namespace_v1" "mesh" {
  for_each = var.mesh_namespaces

  metadata {
    name = each.key

    labels = {
      "istio.io/rev"                     = var.istio_revision
      "app.kubernetes.io/managed-by"     = "terraform"
      "pod-security.kubernetes.io/audit" = "restricted"
      "pod-security.kubernetes.io/warn"  = "restricted"
    }
  }

  depends_on = [helm_release.istiod]
}

resource "kubernetes_resource_quota_v1" "namespace" {
  for_each = var.namespace_resource_policies

  metadata {
    name      = "namespace-capacity"
    namespace = kubernetes_namespace_v1.mesh[each.key].metadata[0].name

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  spec {
    hard = each.value.quota_hard
  }
}

resource "kubernetes_limit_range_v1" "namespace" {
  for_each = var.namespace_resource_policies

  metadata {
    name      = "container-resources"
    namespace = kubernetes_namespace_v1.mesh[each.key].metadata[0].name

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  spec {
    limit {
      type                    = "Container"
      default                 = each.value.container_defaults.limits
      default_request         = each.value.container_defaults.requests
      max                     = each.value.container_defaults.max
      min                     = each.value.container_defaults.min
      max_limit_request_ratio = each.value.container_defaults.max_limit_request_ratio
    }
  }
}

resource "kubernetes_priority_class_v1" "workload" {
  for_each = var.priority_classes

  metadata {
    name = each.key

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  value             = each.value.value
  description       = each.value.description
  global_default    = each.value.global_default
  preemption_policy = each.value.preemption_policy
}

resource "kubernetes_pod_disruption_budget_v1" "workload" {
  for_each = var.pod_disruption_budgets

  metadata {
    name      = each.key
    namespace = kubernetes_namespace_v1.mesh[each.value.namespace].metadata[0].name

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  spec {
    min_available   = each.value.min_available
    max_unavailable = each.value.max_unavailable

    selector {
      match_labels = each.value.selector_labels
    }
  }
}

resource "kubernetes_manifest" "strict_mtls" {
  for_each = var.mesh_namespaces

  manifest = {
    apiVersion = "security.istio.io/v1"
    kind       = "PeerAuthentication"
    metadata = {
      name      = "default"
      namespace = kubernetes_namespace_v1.mesh[each.key].metadata[0].name
    }
    spec = {
      mtls = {
        mode = "STRICT"
      }
    }
  }

  depends_on = [helm_release.istiod]
}

resource "kubernetes_namespace_v1" "monitoring" {
  metadata {
    name = "monitoring"

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }


  depends_on = [kubernetes_manifest.vpc_cni_eni_config]
}

resource "kubernetes_cluster_role_v1" "monitoring_agent_nodes" {
  metadata {
    name = "monitoring-agent-node-reader"

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  rule {
    api_groups = [""]
    resources  = ["nodes"]
    verbs      = ["get", "list"]
  }
}

resource "kubernetes_cluster_role_binding_v1" "monitoring_agent_nodes" {
  metadata {
    name = "monitoring-agent-node-reader"

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role_v1.monitoring_agent_nodes.metadata[0].name
  }

  subject {
    kind      = "Group"
    name      = "monitoring-agent-readers"
    api_group = "rbac.authorization.k8s.io"
  }
}

resource "kubernetes_role_v1" "monitoring_agent_workload" {
  for_each = var.mesh_namespaces

  metadata {
    name      = "monitoring-agent-workload-reader"
    namespace = kubernetes_namespace_v1.mesh[each.key].metadata[0].name

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  rule {
    api_groups = [""]
    resources  = ["events", "pods"]
    verbs      = ["get", "list"]
  }

  rule {
    api_groups = ["apps"]
    resources  = ["daemonsets", "deployments", "replicasets", "statefulsets"]
    verbs      = ["get", "list"]
  }

  rule {
    api_groups = ["autoscaling"]
    resources  = ["horizontalpodautoscalers"]
    verbs      = ["get", "list"]
  }

  rule {
    api_groups = ["policy"]
    resources  = ["poddisruptionbudgets"]
    verbs      = ["get", "list"]
  }
}

resource "kubernetes_role_binding_v1" "monitoring_agent_workload" {
  for_each = var.mesh_namespaces

  metadata {
    name      = "monitoring-agent-workload-reader"
    namespace = kubernetes_namespace_v1.mesh[each.key].metadata[0].name

    labels = {
      "app.kubernetes.io/managed-by" = "terraform"
    }
  }

  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "Role"
    name      = kubernetes_role_v1.monitoring_agent_workload[each.key].metadata[0].name
  }

  subject {
    kind      = "Group"
    name      = "monitoring-agent-readers"
    api_group = "rbac.authorization.k8s.io"
  }
}

resource "helm_release" "kube_prometheus_stack" {
  name       = "kube-prometheus-stack"
  namespace  = kubernetes_namespace_v1.monitoring.metadata[0].name
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "kube-prometheus-stack"
  version    = var.prometheus_stack_chart_version
  atomic     = true
  timeout    = 900

  values = [yamlencode({
    grafana = {
      adminPassword = var.grafana_admin_password
      persistence = {
        enabled = true
        size    = "10Gi"
      }
      ingress = {
        enabled = false
      }
    }
    prometheus = {
      prometheusSpec = {
        retention = var.prometheus_retention
        storageSpec = {
          volumeClaimTemplate = {
            spec = {
              accessModes = ["ReadWriteOnce"]
              resources = {
                requests = {
                  storage = "50Gi"
                }
              }
            }
          }
        }
      }
    }
    alertmanager = {
      enabled = true
    }
  })]
}
