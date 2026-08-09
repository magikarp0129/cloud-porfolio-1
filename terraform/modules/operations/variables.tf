variable "name" {
  description = "Name prefix for operations resources."
  type        = string
}

variable "environment" {
  description = "Environment tag value targeted by automation."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.environment)
    error_message = "environment must be dev, stg, or prod."
  }
}

variable "alarm_topic_arn" {
  description = "SNS topic ARN for automation failure notifications."
  type        = string
}

variable "backup_kms_key_arn" {
  description = "KMS key ARN used by the backup vault."
  type        = string
}

variable "backup_schedule" {
  description = "AWS Backup cron schedule in UTC."
  type        = string
  default     = "cron(0 17 * * ? *)"
}

variable "backup_retention_days" {
  description = "Days to retain daily recovery points."
  type        = number
  default     = 35
}

variable "enable_backup_vault_lock" {
  description = "Whether to enforce Backup Vault Lock governance mode."
  type        = bool
  default     = false
}

variable "backup_vault_lock_changeable_days" {
  description = "Days during which Vault Lock can be changed before compliance mode."
  type        = number
  default     = 14
}

variable "enable_instance_scheduler" {
  description = "Whether to create weekday start and stop schedules. Must remain false for prod."
  type        = bool
  default     = false
}

variable "scheduler_dry_run" {
  description = "Whether the scheduler only logs intended actions without changing resources."
  type        = bool
  default     = true
}

variable "schedule_timezone" {
  description = "IANA timezone for the office-hours scheduler."
  type        = string
  default     = "Asia/Seoul"
}

variable "weekday_start_schedule" {
  description = "EventBridge Scheduler expression for weekday start."
  type        = string
  default     = "cron(0 8 ? * MON-FRI *)"
}

variable "weekday_stop_schedule" {
  description = "EventBridge Scheduler expression for weekday stop."
  type        = string
  default     = "cron(0 20 ? * MON-FRI *)"
}

variable "lambda_log_retention_days" {
  description = "Retention for scheduler Lambda logs."
  type        = number
  default     = 30
}

variable "patch_approval_days" {
  description = "Days after release before an approved security patch is installed."
  type        = number
  default     = 7
}

variable "enable_inspector" {
  description = "Whether to enable Inspector v2. Disable when managed centrally by Security Hub administration."
  type        = bool
  default     = false
}
