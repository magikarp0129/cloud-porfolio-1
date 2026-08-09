output "enterprise_cidr" {
  description = "Enterprise regional RFC1918 allocation."
  value       = local.enterprise_cidr
}

output "regional_pool_id" {
  description = "Regional IPAM pool ID."
  value       = aws_vpc_ipam_pool.regional.id
}

output "service_pool_ids" {
  description = "Service IPAM pool IDs."
  value       = { for key, pool in aws_vpc_ipam_pool.service : key => pool.id }
}

output "service_pool_cidrs" {
  description = "Reserved service supernets."
  value       = { for key, pool in local.service_pools : key => pool.cidr }
}

output "service_environment_cidrs" {
  description = "Approved explicit CIDRs for the fifteen service VPC roots."
  value       = local.service_environment_cidrs
}
