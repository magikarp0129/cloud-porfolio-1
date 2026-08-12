terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {}
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

locals {
  common_tags = {
    Environment  = "stg"
    Owner        = "platform-team"
    Service      = "cloud-portfolio"
    CostCenter   = "cloud-platform"
    ManagedBy    = "terraform"
    BackupPolicy = "none"
    Schedule     = "office-hours"
    DataClass    = "internal"
    PatchGroup   = "stg-amazon_linux_2023"
    Compliance   = "baseline"
  }
}

module "environment" {
  source = "../../modules/workload-environment"

  name                                 = "portfolio-stg"
  environment                          = "stg"
  vpc_cidr                             = "10.15.0.0/16"
  az_count                             = 2
  transit_gateway_id                   = var.transit_gateway_id
  interface_endpoint_services          = ["ecr.api", "ecr.dkr", "logs", "ssm", "ssmmessages"]
  monthly_budget_usd                   = var.monthly_budget_usd
  cost_anomaly_threshold_usd           = 100
  alarm_email_addresses                = var.alarm_email_addresses
  enable_instance_scheduler            = true
  scheduler_dry_run                    = var.scheduler_dry_run
  backup_retention_days                = 35
  enable_backup_vault_lock             = false
  eks_cluster_version                  = var.eks_cluster_version
  eks_admin_principal_arns             = var.eks_admin_principal_arns
  eks_control_plane_log_retention_days = 90
  eks_container_log_retention_days     = 90
  eks_node_groups = {
    general = {
      instance_types             = ["m6i.large"]
      capacity_type              = "ON_DEMAND"
      min_size                   = 2
      max_size                   = 5
      desired_size               = 2
      disk_size                  = 50
      max_unavailable_percentage = 25
      patch_group                = "stg-amazon_linux_2023"
      labels                     = { workload = "general" }
    }
  }
}

output "environment" {
  value = module.environment
}
