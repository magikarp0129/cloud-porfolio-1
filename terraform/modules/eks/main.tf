data "aws_partition" "current" {}
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  control_plane_log_group_name = "/aws/eks/${var.name}/cluster"
  container_insights_log_group_names = toset([
    "/aws/containerinsights/${var.name}/application",
    "/aws/containerinsights/${var.name}/dataplane",
    "/aws/containerinsights/${var.name}/host",
    "/aws/containerinsights/${var.name}/performance",
  ])
  container_insights_enabled = contains(keys(var.addons), "amazon-cloudwatch-observability")
  encrypted_log_group_names = setunion(
    toset([local.control_plane_log_group_name]),
    local.container_insights_enabled ? local.container_insights_log_group_names : toset([]),
  )
  encrypted_log_group_arns = [
    for name in local.encrypted_log_group_names :
    "arn:${data.aws_partition.current.partition}:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:${name}"
  ]

  addon_pod_identity_catalog = {
    vpc-cni = {
      service_account = "aws-node"
      policy_arn      = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEKS_CNI_Policy"
    }
    aws-ebs-csi-driver = {
      service_account = "ebs-csi-controller-sa"
      policy_arn      = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
    }
    amazon-cloudwatch-observability = {
      service_account = "cloudwatch-agent"
      policy_arn      = "arn:${data.aws_partition.current.partition}:iam::aws:policy/CloudWatchAgentServerPolicy"
    }
  }
  addon_pod_identity = {
    for name, config in local.addon_pod_identity_catalog : name => config
    if contains(keys(var.addons), name)
  }
}

data "aws_iam_policy_document" "eks_kms" {
  statement {
    sid       = "EnableAccountAdministration"
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  statement {
    sid    = "AllowAccountUseThroughEC2"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey*",
      "kms:ReEncrypt*",
    ]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "StringEquals"
      variable = "kms:CallerAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["ec2.${data.aws_region.current.name}.amazonaws.com"]
    }
  }

  statement {
    sid       = "AllowAWSResourceGrants"
    effect    = "Allow"
    actions   = ["kms:CreateGrant"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["*"]
    }

    condition {
      test     = "StringEquals"
      variable = "kms:CallerAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }

    condition {
      test     = "Bool"
      variable = "kms:GrantIsForAWSResource"
      values   = ["true"]
    }
  }
}

resource "aws_kms_key" "eks" {
  description             = "${var.name} Kubernetes secrets and node volume encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.eks_kms.json

  tags = {
    Name = "${var.name}-eks"
  }
}

resource "aws_kms_alias" "eks" {
  name          = "alias/${var.name}-eks"
  target_key_id = aws_kms_key.eks.key_id
}

data "aws_iam_policy_document" "cloudwatch_logs_kms" {
  statement {
    sid       = "EnableAccountAdministration"
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  statement {
    sid    = "AllowCloudWatchLogsEncryption"
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:Describe*",
      "kms:Encrypt",
      "kms:GenerateDataKey*",
      "kms:ReEncrypt*",
    ]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["logs.${data.aws_region.current.name}.${data.aws_partition.current.dns_suffix}"]
    }

    condition {
      test     = "ArnEquals"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = local.encrypted_log_group_arns
    }
  }
}

resource "aws_kms_key" "cloudwatch_logs" {
  description             = "${var.name} EKS and Container Insights CloudWatch Logs encryption"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.cloudwatch_logs_kms.json

  tags = {
    Name = "${var.name}-cloudwatch-logs"
  }
}

resource "aws_kms_alias" "cloudwatch_logs" {
  name          = "alias/${var.name}-cloudwatch-logs"
  target_key_id = aws_kms_key.cloudwatch_logs.key_id
}

data "aws_iam_policy_document" "cluster_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "cluster" {
  name               = "${var.name}-cluster"
  assume_role_policy = data.aws_iam_policy_document.cluster_assume_role.json
}

resource "aws_iam_role_policy_attachment" "cluster" {
  role       = aws_iam_role.cluster.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEKSClusterPolicy"
}

resource "aws_cloudwatch_log_group" "cluster" {
  name              = local.control_plane_log_group_name
  retention_in_days = var.control_plane_log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn
}

resource "aws_cloudwatch_log_group" "container_insights" {
  for_each = local.container_insights_enabled ? local.container_insights_log_group_names : toset([])

  name              = each.value
  retention_in_days = var.container_log_retention_days
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn
}

resource "aws_eks_cluster" "this" {
  name     = var.name
  role_arn = aws_iam_role.cluster.arn
  version  = var.cluster_version

  enabled_cluster_log_types = var.control_plane_log_types

  access_config {
    authentication_mode                         = "API_AND_CONFIG_MAP"
    bootstrap_cluster_creator_admin_permissions = var.bootstrap_cluster_creator_admin_permissions
  }

  encryption_config {
    provider {
      key_arn = aws_kms_key.eks.arn
    }
    resources = ["secrets"]
  }

  vpc_config {
    endpoint_private_access = true
    endpoint_public_access  = var.endpoint_public_access
    public_access_cidrs     = var.endpoint_public_access ? var.endpoint_public_access_cidrs : []
    subnet_ids              = var.cluster_subnet_ids
  }

  depends_on = [
    aws_cloudwatch_log_group.cluster,
    aws_iam_role_policy_attachment.cluster,
  ]

  lifecycle {
    precondition {
      condition     = var.bootstrap_cluster_creator_admin_permissions || length(var.admin_principal_arns) > 0
      error_message = "Provide at least one admin_principal_arn when bootstrap creator admin is disabled."
    }

    precondition {
      condition     = !var.endpoint_public_access || length(var.endpoint_public_access_cidrs) > 0
      error_message = "Public endpoint access requires at least one explicit CIDR."
    }
  }
}

resource "aws_eks_access_entry" "admin" {
  for_each = var.admin_principal_arns

  cluster_name  = aws_eks_cluster.this.name
  principal_arn = each.value
  type          = "STANDARD"
}

resource "aws_eks_access_policy_association" "admin" {
  for_each = var.admin_principal_arns

  cluster_name  = aws_eks_cluster.this.name
  principal_arn = each.value
  policy_arn    = "arn:${data.aws_partition.current.partition}:eks::aws:cluster-access-policy/AmazonEKSClusterAdminPolicy"

  access_scope {
    type = "cluster"
  }

  depends_on = [aws_eks_access_entry.admin]
}

data "aws_iam_policy_document" "node_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "node" {
  name               = "${var.name}-node"
  assume_role_policy = data.aws_iam_policy_document.node_assume_role.json
}

resource "aws_iam_role_policy_attachment" "node" {
  for_each = toset([
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonEKSWorkerNodePolicy",
    "arn:${data.aws_partition.current.partition}:iam::aws:policy/AmazonSSMManagedInstanceCore",
  ])

  role       = aws_iam_role.node.name
  policy_arn = each.value
}

resource "aws_launch_template" "node" {
  for_each = var.node_groups

  name_prefix            = "${var.name}-${each.key}-"
  update_default_version = true

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      delete_on_termination = true
      encrypted             = true
      kms_key_id            = aws_kms_key.eks.arn
      volume_size           = each.value.disk_size
      volume_type           = "gp3"
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_put_response_hop_limit = 2
    http_tokens                 = "required"
    instance_metadata_tags      = "disabled"
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = merge(
      { Name = "${var.name}-${each.key}" },
      each.value.patch_group != null ? { PatchGroup = each.value.patch_group } : {},
    )
  }

  tag_specifications {
    resource_type = "volume"
    tags = {
      Name         = "${var.name}-${each.key}"
      BackupPolicy = "daily"
    }
  }
}

resource "aws_eks_node_group" "this" {
  for_each = var.node_groups

  cluster_name         = aws_eks_cluster.this.name
  node_group_name      = each.key
  node_role_arn        = aws_iam_role.node.arn
  subnet_ids           = var.node_subnet_ids
  ami_type             = each.value.ami_type
  capacity_type        = each.value.capacity_type
  force_update_version = each.value.force_update_version
  instance_types       = each.value.instance_types
  labels               = each.value.labels
  release_version      = each.value.release_version
  version              = coalesce(each.value.kubernetes_version, var.cluster_version)

  launch_template {
    id      = aws_launch_template.node[each.key].id
    version = aws_launch_template.node[each.key].latest_version
  }

  scaling_config {
    desired_size = each.value.desired_size
    max_size     = each.value.max_size
    min_size     = each.value.min_size
  }

  update_config {
    max_unavailable_percentage = each.value.max_unavailable_percentage
  }

  dynamic "taint" {
    for_each = each.value.taints

    content {
      key    = taint.value.key
      value  = taint.value.value
      effect = taint.value.effect
    }
  }

  depends_on = [aws_iam_role_policy_attachment.node]

  lifecycle {
    ignore_changes = [scaling_config[0].desired_size]
  }
}

data "aws_iam_policy_document" "pod_identity_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:TagSession"]

    principals {
      type        = "Service"
      identifiers = ["pods.eks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "addon" {
  for_each = local.addon_pod_identity

  name               = "${var.name}-${replace(each.key, "_", "-")}"
  assume_role_policy = data.aws_iam_policy_document.pod_identity_assume_role.json
}

resource "aws_iam_role_policy_attachment" "addon" {
  for_each = local.addon_pod_identity

  role       = aws_iam_role.addon[each.key].name
  policy_arn = each.value.policy_arn
}

data "aws_iam_policy_document" "cloudwatch_agent_kms" {
  count = local.container_insights_enabled ? 1 : 0

  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:DescribeKey",
      "kms:Encrypt",
      "kms:GenerateDataKey*",
      "kms:ReEncrypt*",
    ]
    resources = [aws_kms_key.cloudwatch_logs.arn]

    condition {
      test     = "StringEquals"
      variable = "kms:ViaService"
      values   = ["logs.${data.aws_region.current.name}.${data.aws_partition.current.dns_suffix}"]
    }
  }
}

resource "aws_iam_role_policy" "cloudwatch_agent_kms" {
  count = local.container_insights_enabled ? 1 : 0

  name   = "cloudwatch-logs-kms"
  role   = aws_iam_role.addon["amazon-cloudwatch-observability"].id
  policy = data.aws_iam_policy_document.cloudwatch_agent_kms[0].json
}

data "aws_eks_addon_version" "this" {
  for_each = var.addons

  addon_name         = each.key
  kubernetes_version = aws_eks_cluster.this.version
  most_recent        = each.value.use_most_recent_version
}

resource "aws_eks_addon" "this" {
  for_each = var.addons

  cluster_name                = aws_eks_cluster.this.name
  addon_name                  = each.key
  addon_version               = coalesce(each.value.version, data.aws_eks_addon_version.this[each.key].version)
  configuration_values        = length(each.value.configuration_values) > 0 ? jsonencode(each.value.configuration_values) : null
  resolve_conflicts_on_create = each.value.resolve_conflicts_on_create
  resolve_conflicts_on_update = each.value.resolve_conflicts_on_update

  dynamic "pod_identity_association" {
    for_each = contains(keys(local.addon_pod_identity), each.key) ? [local.addon_pod_identity[each.key]] : []

    content {
      role_arn        = aws_iam_role.addon[each.key].arn
      service_account = pod_identity_association.value.service_account
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.container_insights,
    aws_eks_node_group.this,
    aws_iam_role_policy_attachment.addon,
    aws_iam_role_policy.cloudwatch_agent_kms,
  ]
}

data "tls_certificate" "oidc" {
  url = aws_eks_cluster.this.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "this" {
  url             = aws_eks_cluster.this.identity[0].oidc[0].issuer
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.oidc.certificates[0].sha1_fingerprint]
}
