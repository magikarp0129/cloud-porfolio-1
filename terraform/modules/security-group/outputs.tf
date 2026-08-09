output "security_group_id" {
  description = "Created or externally supplied security group ID."
  value       = local.security_group_id
}

output "ingress_rule_ids" {
  description = "Ingress rule IDs keyed by semantic rule name."
  value       = { for key, rule in aws_vpc_security_group_ingress_rule.this : key => rule.id }
}

output "egress_rule_ids" {
  description = "Egress rule IDs keyed by semantic rule name."
  value       = { for key, rule in aws_vpc_security_group_egress_rule.this : key => rule.id }
}
