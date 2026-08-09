resource "aws_organizations_organization" "this" {
  aws_service_access_principals = var.aws_service_access_principals
  enabled_policy_types          = var.enabled_policy_types
  feature_set                   = "ALL"
}

locals {
  root_organizational_units = {
    for key, ou in var.organizational_units : key => ou if ou.parent_key == null
  }
  child_organizational_units = {
    for key, ou in var.organizational_units : key => ou if ou.parent_key != null
  }
}

resource "aws_organizations_organizational_unit" "root" {
  for_each = local.root_organizational_units

  name      = each.value.name
  parent_id = aws_organizations_organization.this.roots[0].id
}

resource "aws_organizations_organizational_unit" "child" {
  for_each = local.child_organizational_units

  name      = each.value.name
  parent_id = aws_organizations_organizational_unit.root[each.value.parent_key].id
}
