output "vpc_id" {
  description = "Environment VPC ID."
  value       = module.network.vpc_id
}

output "subnet_ids" {
  description = "Environment subnet IDs grouped by LB, AP, DB, Node, Pod, TGW and EKS cluster tier."
  value = {
    lb          = module.network.lb_subnet_ids
    ap          = module.network.ap_subnet_ids
    db          = module.network.db_subnet_ids
    node        = module.network.node_subnet_ids
    pod         = module.network.pod_subnet_ids
    tgw         = module.network.tgw_subnet_ids
    eks_cluster = module.network.eks_cluster_subnet_ids
  }
}

output "transit_gateway_attachment_id" {
  description = "Environment VPC Transit Gateway attachment ID."
  value       = module.network.transit_gateway_attachment_id
}

output "route_table_ids" {
  description = "Environment route-table IDs grouped by LB, AP, DB, Node, Pod, TGW and EKS cluster tier."
  value       = module.network.route_table_ids
}

output "eks_cluster_security_group_id" {
  description = "EKS primary cluster security group ID for VPC CNI ENIConfig."
  value       = try(module.eks[0].cluster_primary_security_group_id, null)
}

output "alarm_topic_arn" {
  description = "Shared operations and cost alarm topic ARN."
  value       = module.observability.alarm_topic_arn
}

output "eks_cluster_name" {
  description = "EKS cluster name, or null when disabled."
  value       = try(module.eks[0].cluster_name, null)
}

output "backup_vault_name" {
  description = "AWS Backup vault name."
  value       = module.operations.backup_vault_name
}
