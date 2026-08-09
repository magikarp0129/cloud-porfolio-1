variable "name" {
  description = "Name prefix for WAF resources."
  type        = string
}

variable "scope" {
  description = "WAF scope. Use REGIONAL for ALB/API Gateway and CLOUDFRONT in us-east-1 for CloudFront."
  type        = string
  default     = "REGIONAL"

  validation {
    condition     = contains(["REGIONAL", "CLOUDFRONT"], var.scope)
    error_message = "scope must be REGIONAL or CLOUDFRONT."
  }
}

variable "rate_limit" {
  description = "Requests per five-minute evaluation window allowed from one IP before blocking."
  type        = number
  default     = 2000
}

variable "resource_arns" {
  description = "Regional ALB, API Gateway stage, AppSync, Cognito, or other WAF-associable resource ARNs."
  type        = set(string)
  default     = []
}

variable "log_retention_days" {
  description = "WAF log retention in CloudWatch Logs."
  type        = number
  default     = 90
}
