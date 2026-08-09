variable "name" {
  description = "Name prefix for IAM resources."
  type        = string
}

variable "deployment_trusted_principal_arns" {
  description = "AWS principal ARNs allowed to assume the Terraform deployment role."
  type        = list(string)
  default     = []
}

variable "deployment_policy_arns" {
  description = "Managed policy ARNs attached to the deployment role. Keep this list environment-specific."
  type        = set(string)
  default     = []
}

variable "permissions_boundary_arn" {
  description = "Optional permissions boundary applied to created roles."
  type        = string
  default     = null
}

variable "audit_trusted_principal_arns" {
  description = "AWS principal ARNs allowed to assume the audit role."
  type        = list(string)
  default     = []
}

variable "github_oidc_provider_arn" {
  description = "Existing GitHub Actions OIDC provider ARN."
  type        = string
  default     = null
}

variable "github_subjects" {
  description = "Allowed GitHub OIDC sub claims such as repo:org/repo:environment:prod."
  type        = list(string)
  default     = []
}

variable "enable_break_glass_role" {
  description = "Whether to create a tightly trusted emergency administrator role."
  type        = bool
  default     = false
}

variable "break_glass_trusted_principal_arns" {
  description = "Principals allowed to assume the emergency role with MFA."
  type        = list(string)
  default     = []
}
