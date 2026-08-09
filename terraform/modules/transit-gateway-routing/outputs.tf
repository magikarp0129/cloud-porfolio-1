output "service_route_table_association_ids" {
  description = "TGW route table association IDs keyed by service attachment."
  value       = { for key, association in aws_ec2_transit_gateway_route_table_association.service : key => association.id }
}
