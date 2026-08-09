variable "aws_region" {
  type    = string
  default = "ap-northeast-2"
}

variable "cluster_name" {
  type    = string
  default = "portfolio-stg-eks"
}

variable "vpc_cni_pod_subnet_ids" {
  description = "Foundation output environment.subnet_ids.pod, keyed by availability-zone name."
  type        = map(string)
}

variable "vpc_cni_security_group_ids" {
  description = "Security groups for Pod secondary ENIs; include environment.eks_cluster_security_group_id."
  type        = set(string)
}

variable "istio_version" {
  description = "Pinned supported Istio patch version promoted from dev."
  type        = string
  default     = "1.30.1"
}

variable "prometheus_stack_chart_version" {
  description = "Pinned kube-prometheus-stack chart version promoted from dev."
  type        = string
}

variable "grafana_admin_password" {
  description = "Grafana bootstrap password supplied through a secret variable."
  type        = string
  sensitive   = true
}
