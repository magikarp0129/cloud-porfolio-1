variable "aws_service_access_principals" {
  description = "AWS service principals allowed to integrate with AWS Organizations."
  type        = list(string)
  default = [
    "cloudtrail.amazonaws.com",
    "config.amazonaws.com",
    "guardduty.amazonaws.com",
    "securityhub.amazonaws.com",
    "inspector2.amazonaws.com"
  ]
}

variable "enabled_policy_types" {
  description = "Organization policy types enabled at the root."
  type        = list(string)
  default     = ["SERVICE_CONTROL_POLICY", "TAG_POLICY"]
}

variable "organizational_units" {
  description = "Organizational units to create under the organization root."
  type = map(object({
    name       = string
    parent_key = optional(string)
  }))

  validation {
    condition = alltrue([
      for key, ou in var.organizational_units :
      ou.parent_key == null || (
        contains(keys(var.organizational_units), ou.parent_key) &&
        try(var.organizational_units[ou.parent_key].parent_key, null) == null
      )
    ])
    error_message = "Every parent_key must reference a root-level organizational unit."
  }
}
