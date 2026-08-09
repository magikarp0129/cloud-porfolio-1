output "root_id" {
  description = "AWS Organizations root ID."
  value       = aws_organizations_organization.this.roots[0].id
}

output "organizational_unit_ids" {
  description = "Organizational unit IDs keyed by logical OU name."
  value = {
    for key, ou in merge(
      aws_organizations_organizational_unit.root,
      aws_organizations_organizational_unit.child,
    ) : key => ou.id
  }
}
