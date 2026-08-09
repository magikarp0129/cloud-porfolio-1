output "policy_ids" {
  description = "SCP policy IDs keyed by logical policy name."
  value = {
    for key, policy in aws_organizations_policy.this :
    key => policy.id
  }
}

