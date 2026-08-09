output "cluster_name" {
  description = "EKS cluster name."
  value       = aws_eks_cluster.this.name
}

output "cluster_primary_security_group_id" {
  description = "EKS-created primary cluster security group ID."
  value       = aws_eks_cluster.this.vpc_config[0].cluster_security_group_id
}

output "cluster_arn" {
  description = "EKS cluster ARN."
  value       = aws_eks_cluster.this.arn
}

output "cluster_endpoint" {
  description = "Kubernetes API endpoint."
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_certificate_authority_data" {
  description = "Base64-encoded cluster CA data."
  value       = aws_eks_cluster.this.certificate_authority[0].data
  sensitive   = true
}

output "oidc_provider_arn" {
  description = "IAM OIDC provider ARN for workloads that still require IRSA."
  value       = aws_iam_openid_connect_provider.this.arn
}

output "node_role_arn" {
  description = "Shared EKS managed node role ARN."
  value       = aws_iam_role.node.arn
}

output "addon_versions" {
  description = "Resolved EKS managed add-on versions."
  value       = { for name, addon in aws_eks_addon.this : name => addon.addon_version }
}

output "control_plane_log_group_name" {
  description = "CloudWatch log group that retains EKS control plane logs."
  value       = aws_cloudwatch_log_group.cluster.name
}

output "control_plane_log_group_arn" {
  description = "CloudWatch log group ARN for EKS control plane logs."
  value       = aws_cloudwatch_log_group.cluster.arn
}

output "container_insights_log_group_names" {
  description = "CloudWatch log groups managed for EKS application, data-plane, host, and performance logs."
  value       = sort(keys(aws_cloudwatch_log_group.container_insights))
}

output "container_insights_log_group_arns" {
  description = "CloudWatch log group ARNs for EKS application, data-plane, host, and performance logs."
  value       = sort([for group in values(aws_cloudwatch_log_group.container_insights) : group.arn])
}

output "cloudwatch_logs_kms_key_arn" {
  description = "Customer-managed KMS key used by EKS CloudWatch log groups."
  value       = aws_kms_key.cloudwatch_logs.arn
}
