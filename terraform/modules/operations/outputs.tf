output "backup_vault_name" {
  description = "AWS Backup vault name."
  value       = aws_backup_vault.this.name
}

output "backup_plan_id" {
  description = "Daily backup plan ID."
  value       = aws_backup_plan.daily.id
}

output "scheduler_function_arn" {
  description = "Instance scheduler Lambda ARN, or null when disabled."
  value       = try(aws_lambda_function.scheduler[0].arn, null)
}

output "patch_baseline_ids" {
  description = "SSM patch baseline IDs keyed by OS family."
  value       = { for key, baseline in aws_ssm_patch_baseline.this : key => baseline.id }
}
