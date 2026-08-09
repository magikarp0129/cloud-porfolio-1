variable "name" {
  description = "Name prefix for the diagnostic role."
  type        = string
}

variable "trusted_principal_arns" {
  description = "Exact AI Tool Broker principal ARNs trusted to assume the diagnostic role. An empty list disables the role."
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for arn in var.trusted_principal_arns : can(regex("^arn:[^:]+:iam::[0-9]{12}:role/.+$", arn))
    ])
    error_message = "trusted_principal_arns must contain exact IAM role ARNs."
  }
}

variable "source_identity_pattern" {
  description = "Required STS SourceIdentity pattern set by the central Tool Broker."
  type        = string
  default     = "req-*"

  validation {
    condition     = startswith(var.source_identity_pattern, "req-") && length(var.source_identity_pattern) <= 64
    error_message = "source_identity_pattern must be a bounded request correlation pattern beginning with req-."
  }
}

variable "cloudwatch_log_group_arns" {
  description = "CloudWatch log group ARNs that approved Logs Insights templates may query."
  type        = set(string)
  default     = []
}

variable "enable_logs_insights" {
  description = "Whether to allow approved Logs Insights queries. Set only when cloudwatch_log_group_arns is non-empty."
  type        = bool
  default     = false
}

variable "eks_cluster_arns" {
  description = "EKS cluster ARNs the broker may describe to establish read-only Kubernetes access."
  type        = set(string)
  default     = []
}

variable "enable_eks_describe" {
  description = "Whether to allow DescribeCluster for the supplied EKS cluster ARNs."
  type        = bool
  default     = false
}

variable "amp_workspace_arns" {
  description = "Optional Amazon Managed Prometheus workspace ARNs available to typed query adapters."
  type        = set(string)
  default     = []
}

variable "enable_amp_queries" {
  description = "Whether to allow typed query access to the supplied AMP workspace ARNs."
  type        = bool
  default     = false
}

variable "permissions_boundary_arn" {
  description = "Optional permissions boundary for the diagnostic role."
  type        = string
  default     = null
}
