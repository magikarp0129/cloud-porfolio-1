output "istio_revision" {
  description = "Installed Istio revision."
  value       = var.istio_revision
}

output "mesh_namespaces" {
  description = "Namespaces enrolled in strict-mTLS service mesh."
  value       = keys(kubernetes_namespace_v1.mesh)
}

output "monitoring_namespace" {
  description = "Namespace containing Prometheus, Alertmanager, and Grafana."
  value       = kubernetes_namespace_v1.monitoring.metadata[0].name
}

output "namespace_resource_policies" {
  description = "Namespaces with Terraform-managed ResourceQuota and LimitRange policies."
  value       = sort(keys(kubernetes_resource_quota_v1.namespace))
}

output "priority_classes" {
  description = "Workload PriorityClass names created by this module."
  value       = sort(keys(kubernetes_priority_class_v1.workload))
}

output "pod_disruption_budgets" {
  description = "PodDisruptionBudgets managed by this module, keyed by input name."
  value = {
    for name, budget in kubernetes_pod_disruption_budget_v1.workload :
    name => budget.metadata[0].namespace
  }
}
