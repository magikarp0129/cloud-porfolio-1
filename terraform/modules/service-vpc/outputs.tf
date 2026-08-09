output "vpc_id" {
  description = "Service VPC ID."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "Service VPC CIDR."
  value       = var.vpc_cidr
}

output "availability_zones" {
  description = "Availability zones selected by the module."
  value       = local.availability_zones
}

output "availability_zone_ids" {
  description = "Stable availability zone IDs selected by the module."
  value       = local.selected_az_ids
}

output "subnet_ids" {
  description = "Subnet IDs grouped by private tier and availability zone."
  value = {
    lb          = { for az, subnet in aws_subnet.lb : az => subnet.id }
    ap          = { for az, subnet in aws_subnet.ap : az => subnet.id }
    db          = { for az, subnet in aws_subnet.db : az => subnet.id }
    node        = { for az, subnet in aws_subnet.node : az => subnet.id }
    pod         = { for az, subnet in aws_subnet.pod : az => subnet.id }
    tgw         = { for az, subnet in aws_subnet.tgw : az => subnet.id }
    eks_cluster = { for az, subnet in aws_subnet.eks_cluster : az => subnet.id }
  }
}

output "subnet_cidrs" {
  description = "Calculated subnet CIDRs grouped by private tier and availability zone."
  value = {
    lb          = local.lb_subnets
    ap          = local.ap_subnets
    db          = local.db_subnets
    node        = local.node_subnets
    pod         = local.pod_subnets
    tgw         = local.tgw_subnets
    eks_cluster = local.eks_cluster_subnets
  }
}

output "transit_gateway_attachment_id" {
  description = "Service VPC Transit Gateway attachment ID."
  value       = aws_ec2_transit_gateway_vpc_attachment.this.id
}
