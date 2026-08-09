terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.0"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = var.aws_region
}

data "aws_eks_cluster" "this" {
  name = var.cluster_name
}

provider "kubernetes" {
  host                   = data.aws_eks_cluster.this.endpoint
  cluster_ca_certificate = base64decode(data.aws_eks_cluster.this.certificate_authority[0].data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", var.cluster_name, "--region", var.aws_region]
  }
}

provider "helm" {
  kubernetes {
    host                   = data.aws_eks_cluster.this.endpoint
    cluster_ca_certificate = base64decode(data.aws_eks_cluster.this.certificate_authority[0].data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", var.cluster_name, "--region", var.aws_region]
    }
  }
}

module "platform" {
  source = "../../../modules/kubernetes-platform"

  name            = "portfolio-prod"
  istio_version   = var.istio_version
  istio_revision  = replace(var.istio_version, ".", "-")
  mesh_namespaces = ["application-prod"]
  vpc_cni_eni_configs = {
    for az, subnet_id in var.vpc_cni_pod_subnet_ids : az => {
      subnet_id          = subnet_id
      security_group_ids = var.vpc_cni_security_group_ids
    }
  }
  namespace_resource_policies = {
    application-prod = {
      quota_hard = {
        "requests.cpu"           = "40"
        "requests.memory"        = "80Gi"
        "limits.cpu"             = "80"
        "limits.memory"          = "160Gi"
        "requests.storage"       = "1Ti"
        "persistentvolumeclaims" = "50"
        "pods"                   = "400"
        "services.loadbalancers" = "8"
      }
      container_defaults = {
        requests = { cpu = "250m", memory = "512Mi" }
        limits   = { cpu = "1", memory = "2Gi" }
        max      = { cpu = "8", memory = "16Gi" }
        min      = { cpu = "50m", memory = "128Mi" }
      }
    }
  }
  prometheus_stack_chart_version = var.prometheus_stack_chart_version
  prometheus_retention           = "30d"
  grafana_admin_password         = var.grafana_admin_password
}
