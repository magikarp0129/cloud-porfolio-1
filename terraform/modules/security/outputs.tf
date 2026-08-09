output "platform_kms_key_arn" {
  description = "KMS key ARN for workload encryption."
  value       = aws_kms_key.platform.arn
}

output "guardduty_detector_id" {
  description = "GuardDuty detector ID, or null when disabled."
  value       = try(aws_guardduty_detector.this[0].id, null)
}
