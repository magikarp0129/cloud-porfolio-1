locals {
  create_security_group = var.security_group_id == null
  security_group_id     = local.create_security_group ? aws_security_group.this[0].id : var.security_group_id
  rule_name_prefix      = var.name != null ? var.name : "existing-sg"
}

resource "aws_security_group" "this" {
  count = local.create_security_group ? 1 : 0

  name_prefix            = var.name != null ? "${var.name}-" : null
  description            = var.description
  vpc_id                 = var.vpc_id
  revoke_rules_on_delete = true

  tags = merge(var.tags, {
    Name = var.name
  })

  lifecycle {
    create_before_destroy = true

    precondition {
      condition     = var.name != null && var.vpc_id != null
      error_message = "name and vpc_id are required when security_group_id is not supplied."
    }
  }
}

resource "aws_vpc_security_group_ingress_rule" "this" {
  for_each = var.ingress_rules

  security_group_id            = local.security_group_id
  description                  = each.value.description
  ip_protocol                  = each.value.ip_protocol
  from_port                    = each.value.from_port
  to_port                      = each.value.to_port
  cidr_ipv4                    = each.value.cidr_ipv4
  cidr_ipv6                    = each.value.cidr_ipv6
  prefix_list_id               = each.value.prefix_list_id
  referenced_security_group_id = each.value.referenced_security_group_id

  tags = merge(var.tags, each.value.tags, {
    Name = "${local.rule_name_prefix}-ingress-${each.key}"
  })
}

resource "aws_vpc_security_group_egress_rule" "this" {
  for_each = var.egress_rules

  security_group_id            = local.security_group_id
  description                  = each.value.description
  ip_protocol                  = each.value.ip_protocol
  from_port                    = each.value.from_port
  to_port                      = each.value.to_port
  cidr_ipv4                    = each.value.cidr_ipv4
  cidr_ipv6                    = each.value.cidr_ipv6
  prefix_list_id               = each.value.prefix_list_id
  referenced_security_group_id = each.value.referenced_security_group_id

  tags = merge(var.tags, each.value.tags, {
    Name = "${local.rule_name_prefix}-egress-${each.key}"
  })
}
