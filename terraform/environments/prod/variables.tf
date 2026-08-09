variable "aws_region" {
  description = "AWS region for the prod environment."
  type        = string
  default     = "ap-northeast-2"
}

variable "transit_gateway_id" {
  description = "Landing Zone Transit Gateway ID for centralized ingress and egress."
  type        = string
}

variable "monthly_budget_usd" {
  description = "Production monthly cost budget."
  type        = number
  default     = 5000
}

variable "alarm_email_addresses" {
  description = "Email addresses that confirm subscriptions to production alerts."
  type        = set(string)
  default     = []
}

variable "eks_cluster_version" {
  description = "EKS Kubernetes minor version."
  type        = string
  default     = "1.35"
}

variable "eks_admin_principal_arns" {
  description = "IAM role ARNs granted EKS administrator access."
  type        = set(string)
}

variable "monitoring_agent_trusted_principal_arns" {
  description = "Central Tool Broker principal ARNs trusted by the production diagnostic role."
  type        = list(string)
  default     = []
}

variable "monitoring_agent_additional_log_group_arns" {
  description = "Production workload log group ARNs available to approved incident query templates."
  type        = set(string)
  default     = []
}

variable "monitoring_agent_permissions_boundary_arn" {
  description = "Optional IAM permissions boundary for the production diagnostic role."
  type        = string
  default     = null
}
