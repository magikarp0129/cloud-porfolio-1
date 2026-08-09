variable "name" {
  description = "Name prefix for the enterprise Transit Gateway."
  type        = string
}

variable "description" {
  description = "Transit Gateway description."
  type        = string
  default     = "Enterprise landing zone Transit Gateway"
}

variable "amazon_side_asn" {
  description = "Private ASN used by the Transit Gateway."
  type        = number
  default     = 64520
}

variable "auto_accept_shared_attachments" {
  description = "Whether RAM-shared VPC attachments are accepted automatically."
  type        = bool
  default     = true
}

variable "create_ram_share" {
  description = "Whether to share the Transit Gateway with AWS RAM."
  type        = bool
  default     = true
}

variable "ram_principals" {
  description = "Organization, OU, or account ARNs/IDs allowed to use the Transit Gateway share."
  type        = set(string)
  default     = []
}

variable "tags" {
  description = "Additional tags."
  type        = map(string)
  default     = {}
}
