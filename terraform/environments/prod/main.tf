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
    Environment  = "prod"
    Owner        = "platform-team"
    Service      = "cloud-portfolio"
    CostCenter   = "cloud-platform"
    ManagedBy    = "terraform"
    BackupPolicy = "daily"
    Schedule     = "always-on"
    DataClass    = "confidential"
    PatchGroup   = "prod-amazon_linux_2023"
    Compliance   = "regulated"
  }
}

module "environment" {
  source = "../../modules/workload-environment"

  name                                       = "portfolio-prod"
  environment                                = "prod"
  vpc_cidr                                   = "10.20.0.0/16"
  az_count                                   = 3
  transit_gateway_id                         = var.transit_gateway_id
  interface_endpoint_services                = ["ecr.api", "ecr.dkr", "ec2", "logs", "monitoring", "ssm", "ssmmessages", "sts"]
  monthly_budget_usd                         = var.monthly_budget_usd
  cost_anomaly_threshold_usd                 = 300
  alarm_email_addresses                      = var.alarm_email_addresses
  enable_instance_scheduler                  = false
  backup_retention_days                      = 35
  enable_backup_vault_lock                   = true
  eks_cluster_version                        = var.eks_cluster_version
  eks_admin_principal_arns                   = var.eks_admin_principal_arns
  eks_control_plane_log_retention_days       = 365
  eks_container_log_retention_days           = 365
  monitoring_agent_trusted_principal_arns    = var.monitoring_agent_trusted_principal_arns
  monitoring_agent_additional_log_group_arns = var.monitoring_agent_additional_log_group_arns
  monitoring_agent_permissions_boundary_arn  = var.monitoring_agent_permissions_boundary_arn
  eks_node_groups = {
    system = {
      instance_types             = ["m7i.large"]
      capacity_type              = "ON_DEMAND"
      min_size                   = 3
      max_size                   = 6
      desired_size               = 3
      disk_size                  = 80
      max_unavailable_percentage = 25
      patch_group                = "prod-amazon_linux_2023"
      labels                     = { workload = "system" }
      taints = [{
        key    = "CriticalAddonsOnly"
        value  = "true"
        effect = "NO_SCHEDULE"
      }]
    }
    application = {
      instance_types             = ["m7i.large", "m6i.large"]
      capacity_type              = "ON_DEMAND"
      min_size                   = 3
      max_size                   = 12
      desired_size               = 3
      disk_size                  = 80
      max_unavailable_percentage = 25
      patch_group                = "prod-amazon_linux_2023"
      labels                     = { workload = "application" }
    }
  }
}

output "environment" {
  value = module.environment
}
