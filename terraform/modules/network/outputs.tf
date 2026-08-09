output "vpc_id" {
  description = "ID of the VPC."
  value       = aws_vpc.this.id
}

output "lb_subnet_ids" {
  description = "Internal load balancer subnet IDs keyed by availability zone."
  value       = { for az, subnet in aws_subnet.lb : az => subnet.id }
}

output "ap_subnet_ids" {
  description = "Application subnet IDs keyed by availability zone."
  value       = { for az, subnet in aws_subnet.ap : az => subnet.id }
}

output "db_subnet_ids" {
  description = "Database subnet IDs keyed by availability zone."
  value       = { for az, subnet in aws_subnet.db : az => subnet.id }
}

output "node_subnet_ids" {
  description = "EKS managed node group subnet IDs keyed by availability zone."
  value       = { for az, subnet in aws_subnet.node : az => subnet.id }
}

output "pod_subnet_ids" {
  description = "VPC CNI custom networking Pod subnet IDs keyed by availability zone."
  value       = { for az, subnet in aws_subnet.pod : az => subnet.id }
}

output "tgw_subnet_ids" {
  description = "Transit Gateway attachment subnet IDs keyed by availability zone."
  value       = { for az, subnet in aws_subnet.tgw : az => subnet.id }
}

output "eks_cluster_subnet_ids" {
  description = "EKS control plane x-ENI subnet IDs keyed by availability zone."
  value       = { for az, subnet in aws_subnet.eks_cluster : az => subnet.id }
}

output "availability_zones" {
  description = "Availability zones used by the VPC."
  value       = local.availability_zones
}

output "route_table_ids" {
  description = "Route table IDs grouped by private subnet tier and availability zone."
  value = {
    lb          = { for az, route_table in aws_route_table.lb : az => route_table.id }
    ap          = { for az, route_table in aws_route_table.ap : az => route_table.id }
    db          = { for az, route_table in aws_route_table.db : az => route_table.id }
    node        = { for az, route_table in aws_route_table.node : az => route_table.id }
    pod         = { for az, route_table in aws_route_table.pod : az => route_table.id }
    tgw         = { for az, route_table in aws_route_table.tgw : az => route_table.id }
    eks_cluster = { for az, route_table in aws_route_table.eks_cluster : az => route_table.id }
  }
}

output "transit_gateway_attachment_id" {
  description = "Transit Gateway attachment ID for the environment VPC."
  value       = aws_ec2_transit_gateway_vpc_attachment.this.id
}
