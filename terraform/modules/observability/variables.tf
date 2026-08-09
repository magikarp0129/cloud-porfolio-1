variable "name" {
  description = "Name prefix for observability resources."
  type        = string
}

variable "vpc_id" {
  description = "VPC ID for Flow Logs."
  type        = string
}

variable "log_retention_days" {
  description = "CloudWatch Logs retention in days."
  type        = number
  default     = 90
}

variable "alarm_email_addresses" {
  description = "Email addresses subscribed to operational alarms. Confirmation is required."
  type        = set(string)
  default     = []
}

variable "rejected_flow_threshold" {
  description = "Rejected network flows within one five-minute period before alarming."
  type        = number
  default     = 100
}

variable "kms_key_arn" {
  description = "Optional customer managed KMS key ARN for CloudWatch Logs."
  type        = string
  default     = null
}
