resource "aws_route" "this" {
  for_each = var.routes

  route_table_id              = lookup(var.route_table_ids, each.value.route_table_key, null)
  destination_cidr_block      = each.value.destination_cidr_block
  destination_ipv6_cidr_block = each.value.destination_ipv6_cidr_block
  destination_prefix_list_id  = each.value.destination_prefix_list_id
  gateway_id                  = each.value.gateway_id
  nat_gateway_id              = each.value.nat_gateway_id
  transit_gateway_id          = each.value.transit_gateway_id
  vpc_peering_connection_id   = each.value.vpc_peering_connection_id
  network_interface_id        = each.value.network_interface_id
  vpc_endpoint_id             = each.value.vpc_endpoint_id
  egress_only_gateway_id      = each.value.egress_only_gateway_id

  lifecycle {
    precondition {
      condition     = contains(keys(var.route_table_ids), each.value.route_table_key)
      error_message = "route_table_key must exist in route_table_ids."
    }
  }
}
