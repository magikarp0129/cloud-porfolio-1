resource "aws_organizations_policy" "this" {
  for_each = var.policies

  name        = each.value.name
  description = each.value.description
  type        = each.value.type
  content     = each.value.content
}

resource "aws_organizations_policy_attachment" "this" {
  for_each = var.attachments

  policy_id = aws_organizations_policy.this[each.value.policy_key].id
  target_id = each.value.target_id
}
