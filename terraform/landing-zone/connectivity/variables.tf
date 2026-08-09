variable "aws_region" {
  description = "AWS Region for TGW route management."
  type        = string
  default     = "ap-northeast-2"
}

variable "route_table_ids" {
  description = "TGW route table IDs from the network-hub apply artifact."
  type        = map(string)
}

variable "service_attachments" {
  description = "Accepted attachment outputs from the fifteen service roots and the three common EKS environment roots."
  type = map(object({
    attachment_id = string
    vpc_cidr      = string
    environment   = string
    service_name  = string
  }))
}

variable "inspection_attachment_id" {
  description = "Central inspection VPC attachment ID when implemented."
  type        = string
  default     = null
}

variable "shared_services_attachment_id" {
  description = "Shared services VPC attachment ID when implemented."
  type        = string
  default     = null
}

variable "enable_inspection_default_routes" {
  description = "Route prod and nonprod default traffic through inspection."
  type        = bool
  default     = false
}

variable "allowed_routes" {
  description = "Explicit service-to-service routes approved by Network and Security."
  type = map(object({
    source_route_table    = string
    destination_cidr      = string
    target_attachment_key = string
  }))
  default = {}
}
