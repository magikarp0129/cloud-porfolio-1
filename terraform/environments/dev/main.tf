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
    Environment  = "dev"
    Owner        = "platform-team"
    Service      = "cloud-portfolio"
    CostCenter   = "cloud-platform"
    ManagedBy    = "terraform"
    BackupPolicy = "none"
    Schedule     = "office-hours"
    DataClass    = "internal"
    PatchGroup   = "dev-amazon_linux_2023"
    Compliance   = "baseline"
  }
}

module "environment" {
  source = "../../modules/workload-environment"

  name                                       = "portfolio-dev"
  environment                                = "dev"
  vpc_cidr                                   = "10.10.0.0/16"
  az_count                                   = 2
  transit_gateway_id                         = var.transit_gateway_id
  interface_endpoint_services                = []
  monthly_budget_usd                         = var.monthly_budget_usd
  cost_anomaly_threshold_usd                 = 50
  alarm_email_addresses                      = var.alarm_email_addresses
  enable_instance_scheduler                  = true
  scheduler_dry_run                          = var.scheduler_dry_run
  backup_retention_days                      = 14
  enable_backup_vault_lock                   = false
  eks_cluster_version                        = var.eks_cluster_version
  eks_admin_principal_arns                   = var.eks_admin_principal_arns
  eks_control_plane_log_retention_days       = 90
  eks_container_log_retention_days           = 30
  monitoring_agent_trusted_principal_arns    = var.monitoring_agent_trusted_principal_arns
  monitoring_agent_additional_log_group_arns = var.monitoring_agent_additional_log_group_arns
  monitoring_agent_permissions_boundary_arn  = var.monitoring_agent_permissions_boundary_arn
  eks_node_groups = {
    general = {
      instance_types             = ["t3.large"]
      capacity_type              = "SPOT"
      min_size                   = 1
      max_size                   = 3
      desired_size               = 1
      disk_size                  = 30
      max_unavailable_percentage = 50
      patch_group                = "dev-amazon_linux_2023"
      labels                     = { workload = "general" }
    }
  }
}

output "environment" {
  value = module.environment
}
