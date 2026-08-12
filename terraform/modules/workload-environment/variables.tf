variable "name" {
  description = "Environment-wide name prefix."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block."
  type        = string
}

variable "az_count" {
  description = "Number of availability zones."
  type        = number
}

variable "transit_gateway_id" {
  description = "Landing Zone Transit Gateway used for centralized ingress and egress."
  type        = string
}

variable "interface_endpoint_services" {
  description = "VPC interface endpoint service suffixes."
  type        = list(string)
  default     = []
}

variable "alarm_email_addresses" {
  description = "Email endpoints for SNS alarms."
  type        = set(string)
  default     = []
}

variable "monthly_budget_usd" {
  description = "Environment monthly budget."
  type        = number
}

variable "cost_anomaly_threshold_usd" {
  description = "Cost anomaly absolute impact threshold."
  type        = number
  default     = 100
}

variable "enable_instance_scheduler" {
  description = "Whether to run the weekday EC2/RDS office-hours scheduler."
  type        = bool
  default     = false
}

variable "scheduler_dry_run" {
  description = "Whether office-hours automation logs actions without changing resources."
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Daily backup retention."
  type        = number
  default     = 35
}

variable "enable_backup_vault_lock" {
  description = "Whether to enforce Backup Vault Lock."
  type        = bool
  default     = false
}

variable "enable_eks" {
  description = "Whether to create an EKS cluster."
  type        = bool
  default     = true
}

variable "eks_cluster_version" {
  description = "EKS Kubernetes minor version."
  type        = string
  default     = "1.35"
}

variable "eks_admin_principal_arns" {
  description = "IAM role ARNs granted EKS cluster administration."
  type        = set(string)
}

variable "eks_control_plane_log_retention_days" {
  description = "Retention for EKS API, audit, authenticator, controller-manager, and scheduler logs."
  type        = number
  default     = 90
}

variable "eks_container_log_retention_days" {
  description = "Retention for EKS Container Insights application, data-plane, host, and performance logs."
  type        = number
  default     = 90
}

variable "eks_node_groups" {
  description = "EKS managed node group definitions."
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
}

variable "deployment_trusted_principal_arns" {
  description = "AWS principals trusted by the Terraform deployment role."
  type        = list(string)
  default     = []
}

variable "deployment_policy_arns" {
  description = "Environment-specific managed policies for the deployment role."
  type        = set(string)
  default     = []
}

variable "audit_trusted_principal_arns" {
  description = "AWS principals trusted by the audit role."
  type        = list(string)
  default     = []
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub Actions OIDC provider ARN."
  type        = string
  default     = null
}

variable "github_subjects" {
  description = "Allowed GitHub Actions OIDC subjects."
  type        = list(string)
  default     = []
}
