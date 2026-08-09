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

  name            = "portfolio-stg"
  istio_version   = var.istio_version
  istio_revision  = replace(var.istio_version, ".", "-")
  mesh_namespaces = ["application-stg"]
  vpc_cni_eni_configs = {
    for az, subnet_id in var.vpc_cni_pod_subnet_ids : az => {
      subnet_id          = subnet_id
      security_group_ids = var.vpc_cni_security_group_ids
    }
  }
  namespace_resource_policies = {
    application-stg = {
      quota_hard = {
        "requests.cpu"           = "12"
        "requests.memory"        = "24Gi"
        "limits.cpu"             = "24"
        "limits.memory"          = "48Gi"
        "requests.storage"       = "250Gi"
        "persistentvolumeclaims" = "20"
        "pods"                   = "150"
        "services.loadbalancers" = "4"
      }
      container_defaults = {
        requests = { cpu = "250m", memory = "256Mi" }
        limits   = { cpu = "1", memory = "1Gi" }
        max      = { cpu = "4", memory = "8Gi" }
        min      = { cpu = "25m", memory = "64Mi" }
      }
    }
  }
  prometheus_stack_chart_version = var.prometheus_stack_chart_version
  prometheus_retention           = "15d"
  grafana_admin_password         = var.grafana_admin_password
}
