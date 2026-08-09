variable "name" {
  description = "EKS cluster name."
  type        = string
}

variable "cluster_version" {
  description = "EKS Kubernetes minor version. Upgrade one minor version at a time."
  type        = string
  default     = "1.35"
}

variable "cluster_subnet_ids" {
  description = "Dedicated subnet IDs used only by EKS control plane x-ENIs."
  type        = list(string)

  validation {
    condition     = length(var.cluster_subnet_ids) >= 2
    error_message = "At least two EKS control plane subnets are required."
  }
}

variable "node_subnet_ids" {
  description = "Dedicated private subnet IDs used by EKS managed node groups."
  type        = list(string)

  validation {
    condition     = length(var.node_subnet_ids) >= 2
    error_message = "At least two EKS node subnets are required."
  }
}

variable "endpoint_public_access" {
  description = "Whether the Kubernetes API endpoint is publicly reachable."
  type        = bool
  default     = false
}

variable "endpoint_public_access_cidrs" {
  description = "CIDRs allowed to reach the public API endpoint when enabled."
  type        = list(string)
  default     = []
}

variable "bootstrap_cluster_creator_admin_permissions" {
  description = "Whether the cluster creator receives bootstrap admin. Disable after access entries are verified."
  type        = bool
  default     = false
}

variable "admin_principal_arns" {
  description = "IAM role ARNs granted EKS cluster administrator access through access entries."
  type        = set(string)
  default     = []
}

variable "control_plane_log_retention_days" {
  description = "Retention for EKS control plane logs."
  type        = number
  default     = 90

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731,
      1096, 1827, 2192, 2557, 2922, 3288, 3653,
    ], var.control_plane_log_retention_days)
    error_message = "control_plane_log_retention_days must be a retention value supported by CloudWatch Logs."
  }
}

variable "control_plane_log_types" {
  description = "EKS control plane log types delivered to CloudWatch Logs."
  type        = set(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  validation {
    condition = length(var.control_plane_log_types) > 0 && length(setsubtract(
      var.control_plane_log_types,
      toset(["api", "audit", "authenticator", "controllerManager", "scheduler"]),
    )) == 0
    error_message = "Enable at least one valid EKS control plane log type."
  }
}

variable "container_log_retention_days" {
  description = "Retention for Container Insights application, data-plane, host, and performance log groups."
  type        = number
  default     = 90

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731,
      1096, 1827, 2192, 2557, 2922, 3288, 3653,
    ], var.container_log_retention_days)
    error_message = "container_log_retention_days must be a retention value supported by CloudWatch Logs."
  }
}

variable "node_groups" {
  description = "Managed node group definitions."
  type = map(object({
    instance_types             = list(string)
    capacity_type              = optional(string, "ON_DEMAND")
    min_size                   = number
    max_size                   = number
    desired_size               = number
    disk_size                  = optional(number, 50)
    ami_type                   = optional(string, "AL2023_x86_64_STANDARD")
    kubernetes_version         = optional(string)
    release_version            = optional(string)
    force_update_version       = optional(bool, false)
    max_unavailable_percentage = optional(number, 25)
    patch_group                = optional(string)
    labels                     = optional(map(string), {})
    taints = optional(list(object({
      key    = string
      value  = optional(string)
      effect = string
    })), [])
  }))

  validation {
    condition = alltrue([
      for group in values(var.node_groups) :
      group.min_size <= group.desired_size && group.desired_size <= group.max_size
    ])
    error_message = "Each node group must satisfy min_size <= desired_size <= max_size."
  }

  validation {
    condition = alltrue([
      for group in values(var.node_groups) :
      group.max_unavailable_percentage >= 1 && group.max_unavailable_percentage <= 100
    ])
    error_message = "Each node group max_unavailable_percentage must be between 1 and 100."
  }
}

variable "addons" {
  description = "EKS managed add-ons. Null versions resolve to the latest compatible version at plan time."
  type = map(object({
    version                     = optional(string)
    use_most_recent_version     = optional(bool, true)
    configuration_values        = optional(any, {})
    resolve_conflicts_on_create = optional(string, "OVERWRITE")
    resolve_conflicts_on_update = optional(string, "PRESERVE")
  }))
  default = {
    vpc-cni = {
      configuration_values = {
        env = {
          AWS_VPC_K8S_CNI_CUSTOM_NETWORK_CFG = "true"
          ENI_CONFIG_LABEL_DEF               = "topology.kubernetes.io/zone"
          ENABLE_PREFIX_DELEGATION           = "true"
          WARM_PREFIX_TARGET                 = "1"
        }
      }
    }
    coredns                = {}
    kube-proxy             = {}
    eks-pod-identity-agent = {}
    aws-ebs-csi-driver     = {}
    amazon-cloudwatch-observability = {
      configuration_values = {
        manager = {
          applicationSignals = {
            autoMonitor = {
              monitorAllServices = false
            }
          }
        }
      }
    }
  }

  validation {
    condition = alltrue([
      for addon in values(var.addons) :
      contains(["NONE", "OVERWRITE"], addon.resolve_conflicts_on_create) &&
      contains(["NONE", "OVERWRITE", "PRESERVE"], addon.resolve_conflicts_on_update)
    ])
    error_message = "Add-on conflict modes must be valid EKS CreateAddon/UpdateAddon values."
  }
}
