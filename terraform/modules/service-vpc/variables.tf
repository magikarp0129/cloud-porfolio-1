variable "name" {
  description = "Name prefix for service network resources."
  type        = string
}

variable "service_name" {
  description = "Stable service name."
  type        = string
}

variable "environment" {
  description = "Environment name."
  type        = string

  validation {
    condition     = contains(["dev", "stg", "prod"], var.environment)
    error_message = "environment must be dev, stg, or prod."
  }
}

variable "workload_profile" {
  description = "Workload profile such as high-growth-eks or small-internal."
  type        = string
}

variable "vpc_cidr" {
  description = "Explicit VPC CIDR allocated by the Landing Zone IPAM catalog."
  type        = string

  validation {
    condition = (
      can(cidrnetmask(var.vpc_cidr)) &&
      tonumber(split("/", var.vpc_cidr)[1]) >= 16 &&
      tonumber(split("/", var.vpc_cidr)[1]) <= 22
    )
    error_message = "vpc_cidr must be a valid IPv4 CIDR between /16 and /22 for the seven private subnet tiers."
  }
}

variable "az_count" {
  description = "Number of availability zones."
  type        = number

  validation {
    condition     = contains([2, 3], var.az_count)
    error_message = "az_count must be 2 or 3."
  }
}

variable "availability_zone_ids" {
  description = "Optional stable AZ IDs such as apne2-az1."
  type        = list(string)
  default     = []

  validation {
    condition     = length(var.availability_zone_ids) == 0 || length(var.availability_zone_ids) == var.az_count
    error_message = "availability_zone_ids must be empty or contain exactly az_count entries."
  }
}

variable "transit_gateway_id" {
  description = "Landing Zone Transit Gateway ID shared with the workload account."
  type        = string
}

variable "landing_zone_default_route_cidr" {
  description = "Destination sent from LB, AP, Node, Pod and EKS cluster subnets to the Landing Zone TGW."
  type        = string
  default     = "0.0.0.0/0"
}

variable "enterprise_cidrs" {
  description = "Enterprise CIDRs reachable from the isolated DB subnets through TGW."
  type        = set(string)
  default     = ["10.64.0.0/10"]
}

variable "tags" {
  description = "Additional tags."
  type        = map(string)
  default     = {}
}
