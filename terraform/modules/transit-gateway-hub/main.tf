locals {
  route_tables = toset(["nonprod", "prod", "shared", "inspection"])
  common_tags = merge(var.tags, {
    ManagedBy = "terraform"
    Component = "transit-gateway"
  })
}

resource "aws_ec2_transit_gateway" "this" {
  description                     = var.description
  amazon_side_asn                 = var.amazon_side_asn
  auto_accept_shared_attachments  = var.auto_accept_shared_attachments ? "enable" : "disable"
  default_route_table_association = "disable"
  default_route_table_propagation = "disable"
  dns_support                     = "enable"
  vpn_ecmp_support                = "enable"

  tags = merge(local.common_tags, {
    Name = var.name
  })
}

resource "aws_ec2_transit_gateway_route_table" "this" {
  for_each = local.route_tables

  transit_gateway_id = aws_ec2_transit_gateway.this.id

  tags = merge(local.common_tags, {
    Name          = "${var.name}-${each.key}"
    RoutingDomain = each.key
  })
}

resource "aws_ram_resource_share" "this" {
  count = var.create_ram_share ? 1 : 0

  name                      = "${var.name}-share"
  allow_external_principals = false

  tags = local.common_tags
}

resource "aws_ram_resource_association" "this" {
  count = var.create_ram_share ? 1 : 0

  resource_arn       = aws_ec2_transit_gateway.this.arn
  resource_share_arn = aws_ram_resource_share.this[0].arn
}

resource "aws_ram_principal_association" "this" {
  for_each = var.create_ram_share ? var.ram_principals : toset([])

  principal          = each.value
  resource_share_arn = aws_ram_resource_share.this[0].arn
}
