output "role_arn" {
  description = "Monitoring diagnostic role ARN, or null when no trusted broker principal is configured."
  value       = try(aws_iam_role.this[0].arn, null)
}

output "role_name" {
  description = "Monitoring diagnostic role name, or null when disabled."
  value       = try(aws_iam_role.this[0].name, null)
}

