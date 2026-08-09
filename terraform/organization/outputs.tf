output "organization_root_id" {
  description = "AWS Organizations root ID."
  value       = module.organization.root_id
}

output "organizational_unit_ids" {
  description = "Organizational unit IDs."
  value       = module.organization.organizational_unit_ids
}

output "policy_ids" {
  description = "Organization policy IDs keyed by logical name."
  value       = module.scp_policy.policy_ids
}
