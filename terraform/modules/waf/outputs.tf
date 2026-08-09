output "web_acl_arn" {
  description = "WAF web ACL ARN."
  value       = aws_wafv2_web_acl.this.arn
}

output "web_acl_id" {
  description = "WAF web ACL ID."
  value       = aws_wafv2_web_acl.this.id
}
