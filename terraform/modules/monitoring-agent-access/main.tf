locals {
  create_role = length(var.trusted_principal_arns) > 0
  log_resources = toset(flatten([
    for arn in var.cloudwatch_log_group_arns : [arn, "${arn}:*"]
  ]))
}

data "aws_iam_policy_document" "assume_role" {
  count = local.create_role ? 1 : 0

  statement {
    sid     = "TrustedToolBrokerOnly"
    effect  = "Allow"
    actions = ["sts:AssumeRole", "sts:SetSourceIdentity"]

    principals {
      type        = "AWS"
      identifiers = var.trusted_principal_arns
    }

    condition {
      test     = "StringLike"
      variable = "sts:SourceIdentity"
      values   = [var.source_identity_pattern]
    }

    condition {
      test     = "StringLike"
      variable = "sts:RoleSessionName"
      values   = [var.source_identity_pattern]
    }
  }
}

resource "aws_iam_role" "this" {
  count = local.create_role ? 1 : 0

  name                 = "${var.name}-monitoring-diagnostic"
  description          = "Short-lived read-only role for approved incident evidence queries"
  assume_role_policy   = data.aws_iam_policy_document.assume_role[0].json
  permissions_boundary = var.permissions_boundary_arn
  max_session_duration = 3600

  tags = {
    AccessType = "monitoring-diagnostic"
    Mutation   = "denied"
  }
}

data "aws_iam_policy_document" "this" {
  count = local.create_role ? 1 : 0

  statement {
    sid    = "IdentityCheck"
    effect = "Allow"
    actions = [
      "sts:GetCallerIdentity",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CloudWatchMetricAlarmAndDashboardRead"
    effect = "Allow"
    actions = [
      "cloudwatch:DescribeAlarmHistory",
      "cloudwatch:DescribeAlarms",
      "cloudwatch:GetDashboard",
      "cloudwatch:GetMetricData",
      "cloudwatch:GetMetricStatistics",
      "cloudwatch:ListDashboards",
      "cloudwatch:ListMetrics",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "CloudWatchLogsQueryControlRead"
    effect = "Allow"
    actions = [
      "logs:DescribeLogGroups",
      "logs:GetLogGroupFields",
      "logs:GetQueryResults",
      "logs:StopQuery",
    ]
    resources = ["*"]
  }

  dynamic "statement" {
    for_each = var.enable_logs_insights ? [1] : []

    content {
      sid       = "ApprovedLogGroupQueries"
      effect    = "Allow"
      actions   = ["logs:StartQuery"]
      resources = local.log_resources
    }
  }

  dynamic "statement" {
    for_each = var.enable_eks_describe ? [1] : []

    content {
      sid       = "ApprovedEKSClusterDescribe"
      effect    = "Allow"
      actions   = ["eks:DescribeCluster"]
      resources = var.eks_cluster_arns
    }
  }

  dynamic "statement" {
    for_each = var.enable_amp_queries ? [1] : []

    content {
      sid    = "ApprovedAMPQueries"
      effect = "Allow"
      actions = [
        "aps:GetLabels",
        "aps:GetMetricMetadata",
        "aps:GetSeries",
        "aps:QueryMetrics",
      ]
      resources = var.amp_workspace_arns
    }
  }

  statement {
    sid    = "DenySensitiveAndInteractiveAccess"
    effect = "Deny"
    actions = [
      "iam:PassRole",
      "kms:Decrypt",
      "logs:Unmask",
      "secretsmanager:GetSecretValue",
      "ssm:GetParameter",
      "ssm:GetParameters",
      "ssm:GetParametersByPath",
      "ssm:SendCommand",
      "ssm:StartAutomationExecution",
      "ssm:StartSession",
      "sts:AssumeRole",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "DenyOperationalMutation"
    effect = "Deny"
    actions = [
      "autoscaling:SetDesiredCapacity",
      "autoscaling:TerminateInstanceInAutoScalingGroup",
      "autoscaling:UpdateAutoScalingGroup",
      "cloudwatch:DeleteAlarms",
      "cloudwatch:DeleteDashboards",
      "cloudwatch:DisableAlarmActions",
      "cloudwatch:EnableAlarmActions",
      "cloudwatch:PutDashboard",
      "cloudwatch:PutMetricAlarm",
      "cloudwatch:SetAlarmState",
      "ec2:ModifyInstanceAttribute",
      "ec2:RebootInstances",
      "ec2:RunInstances",
      "ec2:StartInstances",
      "ec2:StopInstances",
      "ec2:TerminateInstances",
      "eks:AssociateAccessPolicy",
      "eks:CreateAccessEntry",
      "eks:DeleteAccessEntry",
      "eks:DisassociateAccessPolicy",
      "eks:UpdateAccessEntry",
      "eks:UpdateClusterConfig",
      "eks:UpdateClusterVersion",
      "eks:UpdateNodegroupConfig",
      "eks:UpdateNodegroupVersion",
      "elasticloadbalancing:DeleteLoadBalancer",
      "elasticloadbalancing:ModifyLoadBalancerAttributes",
      "elasticloadbalancing:ModifyTargetGroup",
      "elasticloadbalancing:ModifyTargetGroupAttributes",
      "logs:DeleteLogGroup",
      "logs:DeleteLogStream",
      "logs:DeleteRetentionPolicy",
      "logs:PutDataProtectionPolicy",
      "logs:PutLogEvents",
      "logs:PutRetentionPolicy",
      "rds:FailoverDBCluster",
      "rds:ModifyDBCluster",
      "rds:ModifyDBInstance",
      "rds:RebootDBCluster",
      "rds:RebootDBInstance",
      "rds:StartDBCluster",
      "rds:StartDBInstance",
      "rds:StopDBCluster",
      "rds:StopDBInstance",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "this" {
  count = local.create_role ? 1 : 0

  name   = "monitoring-diagnostic-read-only"
  role   = aws_iam_role.this[0].id
  policy = data.aws_iam_policy_document.this[0].json

  lifecycle {
    precondition {
      condition     = !var.enable_logs_insights || length(var.cloudwatch_log_group_arns) > 0
      error_message = "enable_logs_insights requires at least one approved CloudWatch log group ARN."
    }

    precondition {
      condition     = !var.enable_eks_describe || length(var.eks_cluster_arns) > 0
      error_message = "enable_eks_describe requires at least one EKS cluster ARN."
    }

    precondition {
      condition     = !var.enable_amp_queries || length(var.amp_workspace_arns) > 0
      error_message = "enable_amp_queries requires at least one AMP workspace ARN."
    }
  }
}
