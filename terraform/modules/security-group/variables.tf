variable "name" {
  description = "Name prefix when this module creates the security group."
  type        = string
  default     = null
}

variable "description" {
  description = "Security group description when this module creates the group."
  type        = string
  default     = "Managed by Terraform"
}

variable "vpc_id" {
  description = "VPC ID when this module creates the security group."
  type        = string
  default     = null
}

variable "security_group_id" {
  description = "Existing security group ID when this module manages rules only."
  type        = string
  default     = null
}

variable "ingress_rules" {
  description = "Ingress rules keyed by stable semantic names. Exactly one source must be set per rule."
  type = map(object({
    description                  = optional(string)
    ip_protocol                  = string
    from_port                    = optional(number)
    to_port                      = optional(number)
    cidr_ipv4                    = optional(string)
    cidr_ipv6                    = optional(string)
    prefix_list_id               = optional(string)
    referenced_security_group_id = optional(string)
    tags                         = optional(map(string), {})
  }))
  default = {}

  validation {
    condition = alltrue([
      for rule in values(var.ingress_rules) : length(compact([
        rule.cidr_ipv4,
        rule.cidr_ipv6,
        rule.prefix_list_id,
        rule.referenced_security_group_id,
      ])) == 1
    ])
    error_message = "Each ingress rule must set exactly one source: cidr_ipv4, cidr_ipv6, prefix_list_id, or referenced_security_group_id."
  }

  validation {
    condition = alltrue([
      for rule in values(var.ingress_rules) :
      rule.ip_protocol == "-1" || (rule.from_port != null && rule.to_port != null)
    ])
    error_message = "Ingress TCP, UDP, and ICMP rules must define from_port and to_port."
  }
}

variable "egress_rules" {
  description = "Egress rules keyed by stable semantic names. Exactly one destination must be set per rule."
  type = map(object({
    description                  = optional(string)
    ip_protocol                  = string
    from_port                    = optional(number)
    to_port                      = optional(number)
    cidr_ipv4                    = optional(string)
    cidr_ipv6                    = optional(string)
    prefix_list_id               = optional(string)
    referenced_security_group_id = optional(string)
    tags                         = optional(map(string), {})
  }))
  default = {}

  validation {
    condition = alltrue([
      for rule in values(var.egress_rules) : length(compact([
        rule.cidr_ipv4,
        rule.cidr_ipv6,
        rule.prefix_list_id,
        rule.referenced_security_group_id,
      ])) == 1
    ])
    error_message = "Each egress rule must set exactly one destination: cidr_ipv4, cidr_ipv6, prefix_list_id, or referenced_security_group_id."
  }

  validation {
    condition = alltrue([
      for rule in values(var.egress_rules) :
      rule.ip_protocol == "-1" || (rule.from_port != null && rule.to_port != null)
    ])
    error_message = "Egress TCP, UDP, and ICMP rules must define from_port and to_port."
  }
}

variable "tags" {
  description = "Additional tags for the security group and rules."
  type        = map(string)
  default     = {}
}
