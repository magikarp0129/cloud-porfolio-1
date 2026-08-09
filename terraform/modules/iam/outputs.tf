output "deployment_role_arn" {
  description = "Terraform deployment role ARN, or null when disabled."
  value       = try(aws_iam_role.deployment[0].arn, null)
}

output "audit_role_arn" {
  description = "Security audit role ARN, or null when disabled."
  value       = try(aws_iam_role.audit[0].arn, null)
}

output "break_glass_role_arn" {
  description = "Emergency administrator role ARN, or null when disabled."
  value       = try(aws_iam_role.break_glass[0].arn, null)
}
