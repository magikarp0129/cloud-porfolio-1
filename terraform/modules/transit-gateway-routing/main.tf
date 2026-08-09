locals {
  service_route_tables = {
    for key, attachment in var.service_attachments :
    key => attachment.environment == "prod" ? var.route_table_ids["prod"] : var.route_table_ids["nonprod"]
  }

  inspection_return_routes = var.inspection_attachment_id == null ? {} : var.service_attachments
  shared_return_routes     = var.shared_services_attachment_id == null ? {} : var.service_attachments
  inspection_defaults = var.enable_inspection_default_routes && var.inspection_attachment_id != null ? {
    nonprod = var.route_table_ids["nonprod"]
    prod    = var.route_table_ids["prod"]
  } : {}
}

resource "aws_ec2_transit_gateway_route_table_association" "service" {
  for_each = var.service_attachments

  transit_gateway_attachment_id  = each.value.attachment_id
  transit_gateway_route_table_id = local.service_route_tables[each.key]
  replace_existing_association   = true
}

resource "aws_ec2_transit_gateway_route" "inspection_return" {
  for_each = local.inspection_return_routes

  destination_cidr_block         = each.value.vpc_cidr
  transit_gateway_attachment_id  = each.value.attachment_id
  transit_gateway_route_table_id = var.route_table_ids["inspection"]
}

resource "aws_ec2_transit_gateway_route" "shared_return" {
  for_each = local.shared_return_routes

  destination_cidr_block         = each.value.vpc_cidr
  transit_gateway_attachment_id  = each.value.attachment_id
  transit_gateway_route_table_id = var.route_table_ids["shared"]
}

resource "aws_ec2_transit_gateway_route" "inspection_default" {
  for_each = local.inspection_defaults

  destination_cidr_block         = "0.0.0.0/0"
  transit_gateway_attachment_id  = var.inspection_attachment_id
  transit_gateway_route_table_id = each.value
}

resource "aws_ec2_transit_gateway_route" "allowed" {
  for_each = var.allowed_routes

  destination_cidr_block         = each.value.destination_cidr
  transit_gateway_attachment_id  = var.service_attachments[each.value.target_attachment_key].attachment_id
  transit_gateway_route_table_id = var.route_table_ids[each.value.source_route_table]

  lifecycle {
    precondition {
      condition     = contains(keys(var.service_attachments), each.value.target_attachment_key)
      error_message = "allowed route target_attachment_key must exist in service_attachments."
    }
  }
}
