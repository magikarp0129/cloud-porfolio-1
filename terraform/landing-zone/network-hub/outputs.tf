output "transit_gateway_id" {
  description = "TGW ID distributed to approved service deployment pipelines."
  value       = module.transit_gateway.transit_gateway_id
}

output "route_table_ids" {
  description = "Central TGW route table IDs."
  value       = module.transit_gateway.route_table_ids
}

output "ram_resource_share_arn" {
  description = "RAM share ARN for service accounts."
  value       = module.transit_gateway.ram_resource_share_arn
}
