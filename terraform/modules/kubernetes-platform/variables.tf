variable "name" {
  description = "Platform release name prefix."
  type        = string
}

variable "istio_version" {
  description = "Pinned Istio chart version."
  type        = string
}

variable "istio_revision" {
  description = "Istio revision used for canary control-plane upgrades."
  type        = string
}

variable "mesh_namespaces" {
  description = "Application namespaces created with Istio revision injection and strict mTLS."
  type        = set(string)
  default     = []
}

variable "vpc_cni_eni_configs" {
  description = "VPC CNI ENIConfig definitions keyed by availability-zone name. Each entry maps Pods to the dedicated Pod subnet and EKS cluster security group."
  type = map(object({
    subnet_id          = string
    security_group_ids = set(string)
  }))
  default = {}

  validation {
    condition = alltrue([
      for az, config in var.vpc_cni_eni_configs :
      length(trimspace(az)) > 0 &&
      length(trimspace(config.subnet_id)) > 0 &&
      length(config.security_group_ids) > 0
    ])
    error_message = "Each ENIConfig requires an AZ name, a Pod subnet ID, and at least one security group ID."
  }
}

variable "namespace_resource_policies" {
  description = "ResourceQuota and container LimitRange policies keyed by a namespace in mesh_namespaces."
  type = map(object({
    quota_hard = map(string)
    container_defaults = object({
      limits                  = map(string)
      requests                = map(string)
      max                     = optional(map(string), {})
      min                     = optional(map(string), {})
      max_limit_request_ratio = optional(map(string), {})
    })
  }))
  default = {}

  validation {
    condition = alltrue([
      for policy in values(var.namespace_resource_policies) :
      length(policy.quota_hard) > 0 &&
      length(policy.container_defaults.limits) > 0 &&
      length(policy.container_defaults.requests) > 0
    ])
    error_message = "Each namespace resource policy must define a non-empty quota and default container requests and limits."
  }
}

variable "priority_classes" {
  description = "Cluster-scoped workload PriorityClasses. Built-in system-* classes must not be redefined."
  type = map(object({
    value             = number
    description       = string
    global_default    = optional(bool, false)
    preemption_policy = optional(string, "PreemptLowerPriority")
  }))
  default = {
    platform-critical = {
      value             = 1000000
      description       = "Critical platform and availability workloads."
      preemption_policy = "PreemptLowerPriority"
    }
    application-high = {
      value             = 100000
      description       = "Customer-facing application workloads with elevated scheduling priority."
      preemption_policy = "PreemptLowerPriority"
    }
    batch-low = {
      value             = -1000
      description       = "Interruptible batch workloads that must not preempt serving workloads."
      preemption_policy = "Never"
    }
  }

  validation {
    condition = alltrue([
      for name, priority_class in var.priority_classes :
      !startswith(name, "system-") &&
      priority_class.value >= -2147483648 && priority_class.value <= 1000000000 &&
      contains(["Never", "PreemptLowerPriority"], priority_class.preemption_policy)
      ]) && length([
      for priority_class in values(var.priority_classes) : priority_class
      if priority_class.global_default
    ]) <= 1
    error_message = "PriorityClass names, values, preemption policies, and global-default count must satisfy Kubernetes constraints."
  }
}

variable "pod_disruption_budgets" {
  description = "Optional PDBs keyed by name. Selectors must match the owning workload exactly; define these in the application state when it owns that workload."
  type = map(object({
    namespace       = string
    selector_labels = map(string)
    min_available   = optional(string)
    max_unavailable = optional(string)
  }))
  default = {}

  validation {
    condition = alltrue([
      for budget in values(var.pod_disruption_budgets) :
      length(budget.selector_labels) > 0 &&
      ((budget.min_available != null) != (budget.max_unavailable != null))
    ])
    error_message = "Each PDB requires a non-empty selector and exactly one of min_available or max_unavailable."
  }
}

variable "prometheus_stack_chart_version" {
  description = "Pinned kube-prometheus-stack chart version."
  type        = string
}

variable "prometheus_retention" {
  description = "Prometheus metrics retention."
  type        = string
  default     = "15d"
}

variable "grafana_admin_password" {
  description = "Bootstrap Grafana administrator password. Replace with external secret management in production."
  type        = string
  sensitive   = true
}

variable "enable_istio_ingress" {
  description = "Whether to install an Istio ingress gateway."
  type        = bool
  default     = true
}
