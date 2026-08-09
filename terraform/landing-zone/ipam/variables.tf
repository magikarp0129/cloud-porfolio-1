variable "aws_region" {
  description = "AWS Region for the regional IPAM pool."
  type        = string
  default     = "ap-northeast-2"
}

variable "ipam_tier" {
  description = "IPAM tier. Organization-wide enterprise use normally requires advanced capabilities."
  type        = string
  default     = "advanced"

  validation {
    condition     = contains(["free", "advanced"], var.ipam_tier)
    error_message = "ipam_tier must be free or advanced."
  }
}
