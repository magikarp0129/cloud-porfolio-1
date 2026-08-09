module "network" {
  source = "../network"

  name                        = var.name
  cidr_block                  = var.vpc_cidr
  az_count                    = var.az_count
  transit_gateway_id          = var.transit_gateway_id
  enable_s3_gateway_endpoint  = true
  interface_endpoint_services = var.interface_endpoint_services
}

module "security" {
  source = "../security"

  name                             = var.name
  enable_guardduty                 = true
  enable_security_hub              = true
  enable_inspector                 = true
  enable_ebs_encryption_by_default = true
}

module "iam" {
  source = "../iam"

  name                              = var.name
  deployment_trusted_principal_arns = var.deployment_trusted_principal_arns
  deployment_policy_arns            = var.deployment_policy_arns
  audit_trusted_principal_arns      = var.audit_trusted_principal_arns
  github_oidc_provider_arn          = var.github_oidc_provider_arn
  github_subjects                   = var.github_subjects
}

module "observability" {
  source = "../observability"

  name                  = var.name
  vpc_id                = module.network.vpc_id
  kms_key_arn           = module.security.platform_kms_key_arn
  alarm_email_addresses = var.alarm_email_addresses
  log_retention_days    = var.environment == "prod" ? 365 : 90
}

module "operations" {
  source = "../operations"

  name                      = var.name
  environment               = var.environment
  alarm_topic_arn           = module.observability.alarm_topic_arn
  backup_kms_key_arn        = module.security.platform_kms_key_arn
  backup_retention_days     = var.backup_retention_days
  enable_backup_vault_lock  = var.enable_backup_vault_lock
  enable_instance_scheduler = var.enable_instance_scheduler
  scheduler_dry_run         = var.scheduler_dry_run
  enable_inspector          = false
}

module "cost" {
  source = "../cost"

  name                  = var.name
  environment           = var.environment
  monthly_budget_usd    = var.monthly_budget_usd
  alarm_topic_arn       = module.observability.alarm_topic_arn
  anomaly_threshold_usd = var.cost_anomaly_threshold_usd
}

module "eks" {
  count  = var.enable_eks ? 1 : 0
  source = "../eks"

  name                                        = "${var.name}-eks"
  cluster_version                             = var.eks_cluster_version
  cluster_subnet_ids                          = values(module.network.eks_cluster_subnet_ids)
  node_subnet_ids                             = values(module.network.node_subnet_ids)
  endpoint_public_access                      = false
  bootstrap_cluster_creator_admin_permissions = false
  admin_principal_arns                        = var.eks_admin_principal_arns
  control_plane_log_retention_days            = var.eks_control_plane_log_retention_days
  container_log_retention_days                = var.eks_container_log_retention_days
  node_groups                                 = var.eks_node_groups
}

locals {
  monitoring_agent_foundation_log_group_arns = setunion(
    toset([module.observability.vpc_flow_log_group_arn]),
    var.enable_eks ? toset(concat(
      [module.eks[0].control_plane_log_group_arn],
      module.eks[0].container_insights_log_group_arns,
    )) : toset([]),
  )
}

module "monitoring_agent_access" {
  source = "../monitoring-agent-access"

  name                     = var.name
  trusted_principal_arns   = var.monitoring_agent_trusted_principal_arns
  permissions_boundary_arn = var.monitoring_agent_permissions_boundary_arn
  cloudwatch_log_group_arns = setunion(
    local.monitoring_agent_foundation_log_group_arns,
    var.monitoring_agent_additional_log_group_arns,
  )
  enable_logs_insights = true
  eks_cluster_arns     = var.enable_eks ? toset([module.eks[0].cluster_arn]) : toset([])
  enable_eks_describe  = var.enable_eks
}

resource "aws_eks_access_entry" "monitoring_agent" {
  count = var.enable_eks && length(var.monitoring_agent_trusted_principal_arns) > 0 ? 1 : 0

  cluster_name      = module.eks[0].cluster_name
  principal_arn     = module.monitoring_agent_access.role_arn
  kubernetes_groups = ["monitoring-agent-readers"]
  type              = "STANDARD"
}
