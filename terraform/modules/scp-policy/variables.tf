variable "policies" {
  description = "SCP documents keyed by logical policy name."
  type = map(object({
    name        = string
    description = string
    content     = string
    type        = optional(string, "SERVICE_CONTROL_POLICY")
  }))
}

variable "attachments" {
  description = "SCP attachments keyed by logical attachment name."
  type = map(object({
    policy_key = string
    target_id  = string
  }))
}
