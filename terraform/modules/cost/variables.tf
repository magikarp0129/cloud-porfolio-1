variable "name" {
  description = "Name prefix for FinOps resources."
  type        = string
}

variable "environment" {
  description = "Environment tag value used by budget filters."
  type        = string
}

variable "monthly_budget_usd" {
  description = "Monthly cost budget in USD."
  type        = number

  validation {
    condition     = var.monthly_budget_usd > 0
    error_message = "monthly_budget_usd must be greater than zero."
  }
}

variable "alarm_topic_arn" {
  description = "SNS topic ARN for budget and cost anomaly notifications."
  type        = string
}

variable "anomaly_threshold_usd" {
  description = "Absolute cost anomaly impact required before notification."
  type        = number
  default     = 100
}
