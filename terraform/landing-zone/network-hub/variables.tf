variable "aws_region" {
  description = "AWS Region for the network hub."
  type        = string
  default     = "ap-northeast-2"
}

variable "ram_principals" {
  description = "Organization, OU, or workload account principals allowed to use the TGW share."
  type        = set(string)
  default     = []
}
