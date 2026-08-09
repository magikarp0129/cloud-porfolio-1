output "transit_gateway_id" {
  description = "Transit Gateway ID."
  value       = aws_ec2_transit_gateway.this.id
}

output "transit_gateway_arn" {
  description = "Transit Gateway ARN."
  value       = aws_ec2_transit_gateway.this.arn
}

output "route_table_ids" {
  description = "Transit Gateway route table IDs keyed by routing domain."
  value       = { for key, route_table in aws_ec2_transit_gateway_route_table.this : key => route_table.id }
}

output "ram_resource_share_arn" {
  description = "RAM resource share ARN when sharing is enabled."
  value       = try(aws_ram_resource_share.this[0].arn, null)
}
