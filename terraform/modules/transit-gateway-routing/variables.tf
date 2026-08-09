variable "route_table_ids" {
  description = "TGW route table IDs keyed by nonprod, prod, shared, and inspection."
  type        = map(string)

  validation {
    condition     = alltrue([for key in ["nonprod", "prod", "shared", "inspection"] : contains(keys(var.route_table_ids), key)])
    error_message = "route_table_ids must contain nonprod, prod, shared, and inspection."
  }
}

variable "service_attachments" {
  description = "Accepted workload VPC attachments managed by the Network account, including service and common EKS environment roots."
  type = map(object({
    attachment_id = string
    vpc_cidr      = string
    environment   = string
    service_name  = string
  }))

  validation {
    condition     = alltrue([for attachment in values(var.service_attachments) : contains(["dev", "stg", "prod"], attachment.environment)])
    error_message = "Every attachment environment must be dev, stg, or prod."
  }
}

variable "inspection_attachment_id" {
  description = "Optional centralized inspection VPC attachment ID."
  type        = string
  default     = null
}

variable "shared_services_attachment_id" {
  description = "Optional shared services VPC attachment ID."
  type        = string
  default     = null
}

variable "enable_inspection_default_routes" {
  description = "Whether prod and nonprod send their default route to the inspection attachment."
  type        = bool
  default     = false
}

variable "allowed_routes" {
  description = "Explicit service routes. The source routing domain is prod or nonprod."
  type = map(object({
    source_route_table    = string
    destination_cidr      = string
    target_attachment_key = string
  }))
  default = {}

  validation {
    condition     = alltrue([for route in values(var.allowed_routes) : contains(["prod", "nonprod"], route.source_route_table)])
    error_message = "allowed_routes source_route_table must be prod or nonprod."
  }
}
