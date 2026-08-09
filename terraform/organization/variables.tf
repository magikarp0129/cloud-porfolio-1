variable "aws_region" {
  description = "AWS region used for AWS Organizations management operations."
  type        = string
  default     = "us-east-1"
}

variable "approved_regions" {
  description = "Regions approved for workload resource creation."
  type        = list(string)
  default     = ["ap-northeast-2", "us-east-1"]
}

variable "security_admin_role_arn_patterns" {
  description = "Role ARN patterns allowed to administer protected security controls."
  type        = list(string)
  default     = ["arn:aws:iam::*:role/OrganizationSecurityAutomation"]
}
