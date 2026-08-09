output "budget_id" {
  description = "AWS Budgets budget ID."
  value       = aws_budgets_budget.monthly.id
}

output "anomaly_monitor_arn" {
  description = "Cost Explorer anomaly monitor ARN."
  value       = aws_ce_anomaly_monitor.services.arn
}
