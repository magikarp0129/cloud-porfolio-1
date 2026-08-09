variable "name" {
  description = "Name prefix for security resources."
  type        = string
}

variable "enable_guardduty" {
  description = "Whether to enable GuardDuty in this account and region."
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Whether to enable Security Hub in this account and region."
  type        = bool
  default     = true
}

variable "enable_inspector" {
  description = "Whether to enable Inspector v2 scanning."
  type        = bool
  default     = true
}

variable "enable_ebs_encryption_by_default" {
  description = "Whether to enforce default EBS encryption with the module KMS key."
  type        = bool
  default     = true
}

variable "kms_deletion_window_in_days" {
  description = "KMS key deletion waiting period."
  type        = number
  default     = 30

  validation {
    condition     = var.kms_deletion_window_in_days >= 7 && var.kms_deletion_window_in_days <= 30
    error_message = "kms_deletion_window_in_days must be between 7 and 30."
  }
}
