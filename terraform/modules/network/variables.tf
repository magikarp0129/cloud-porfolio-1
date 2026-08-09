variable "name" {
  description = "Name prefix for network resources."
  type        = string
}

variable "cidr_block" {
  description = "CIDR block for the VPC. /16-/22 supports the seven private subnet tiers."
  type        = string

  validation {
    condition = (
      can(cidrnetmask(var.cidr_block)) &&
      tonumber(split("/", var.cidr_block)[1]) >= 16 &&
      tonumber(split("/", var.cidr_block)[1]) <= 22
    )
    error_message = "cidr_block must be a valid IPv4 CIDR between /16 and /22."
  }
}

variable "az_count" {
  description = "Number of availability zones to use."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "az_count must be either 2 or 3 for this portfolio baseline."
  }
}

variable "transit_gateway_id" {
  description = "Landing Zone Transit Gateway used for centralized ingress and egress."
  type        = string
}

variable "centralized_default_route_cidr" {
  description = "Default destination sent from LB, AP, Node, Pod and EKS cluster subnets to the Landing Zone TGW."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enable_s3_gateway_endpoint" {
  description = "Whether to create a no-hourly-cost S3 gateway endpoint."
  type        = bool
  default     = true
}

variable "interface_endpoint_services" {
  description = "Regional AWS interface endpoint service suffixes, for example ssm or ecr.api."
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.interface_endpoint_services) == length(toset(var.interface_endpoint_services))
    error_message = "interface_endpoint_services must not contain duplicates."
  }
}
