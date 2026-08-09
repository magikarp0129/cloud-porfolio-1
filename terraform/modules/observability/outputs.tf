output "alarm_topic_arn" {
  description = "SNS topic ARN used by platform alarms."
  value       = aws_sns_topic.alarms.arn
}

output "vpc_flow_log_group_name" {
  description = "VPC Flow Logs CloudWatch log group name."
  value       = aws_cloudwatch_log_group.vpc_flow_logs.name
}

output "vpc_flow_log_group_arn" {
  description = "VPC Flow Logs CloudWatch log group ARN."
  value       = aws_cloudwatch_log_group.vpc_flow_logs.arn
}

output "dashboard_name" {
  description = "CloudWatch platform dashboard name."
  value       = aws_cloudwatch_dashboard.platform.dashboard_name
}
