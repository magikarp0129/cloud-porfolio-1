data "aws_partition" "current" {}

locals {
  create_deployment_role = length(var.deployment_trusted_principal_arns) > 0 || var.github_oidc_provider_arn != null
  create_audit_role      = length(var.audit_trusted_principal_arns) > 0
}

data "aws_iam_policy_document" "deployment_assume_role" {
  dynamic "statement" {
    for_each = length(var.deployment_trusted_principal_arns) > 0 ? [1] : []

    content {
      sid     = "TrustedAWSPrincipals"
      effect  = "Allow"
      actions = ["sts:AssumeRole"]

      principals {
        type        = "AWS"
        identifiers = var.deployment_trusted_principal_arns
      }
    }
  }

  dynamic "statement" {
    for_each = var.github_oidc_provider_arn != null ? [1] : []

    content {
      sid     = "GitHubActionsOIDC"
      effect  = "Allow"
      actions = ["sts:AssumeRoleWithWebIdentity"]

      principals {
        type        = "Federated"
        identifiers = [var.github_oidc_provider_arn]
      }

      condition {
        test     = "StringEquals"
        variable = "token.actions.githubusercontent.com:aud"
        values   = ["sts.amazonaws.com"]
      }

      condition {
        test     = "StringLike"
        variable = "token.actions.githubusercontent.com:sub"
        values   = var.github_subjects
      }
    }
  }
}

resource "aws_iam_role" "deployment" {
  count = local.create_deployment_role ? 1 : 0

  name                 = "${var.name}-terraform-deployment"
  description          = "Short-lived role used by reviewed Terraform deployments"
  assume_role_policy   = data.aws_iam_policy_document.deployment_assume_role.json
  permissions_boundary = var.permissions_boundary_arn
  max_session_duration = 3600

  tags = {
    AccessType = "deployment"
  }

  lifecycle {
    precondition {
      condition     = var.github_oidc_provider_arn == null || length(var.github_subjects) > 0
      error_message = "github_subjects cannot be empty when GitHub OIDC trust is enabled."
    }
  }
}

resource "aws_iam_role_policy_attachment" "deployment" {
  for_each = local.create_deployment_role ? var.deployment_policy_arns : []

  role       = aws_iam_role.deployment[0].name
  policy_arn = each.value
}

data "aws_iam_policy_document" "audit_assume_role" {
  count = local.create_audit_role ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = var.audit_trusted_principal_arns
    }
  }
}

resource "aws_iam_role" "audit" {
  count = local.create_audit_role ? 1 : 0

  name                 = "${var.name}-security-audit"
  description          = "Read-only role for security and compliance review"
  assume_role_policy   = data.aws_iam_policy_document.audit_assume_role[0].json
  permissions_boundary = var.permissions_boundary_arn
  max_session_duration = 3600

  tags = {
    AccessType = "audit"
  }
}

resource "aws_iam_role_policy_attachment" "audit_read_only" {
  count = local.create_audit_role ? 1 : 0

  role       = aws_iam_role.audit[0].name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/ReadOnlyAccess"
}

resource "aws_iam_role_policy_attachment" "audit_security" {
  count = local.create_audit_role ? 1 : 0

  role       = aws_iam_role.audit[0].name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/SecurityAudit"
}

data "aws_iam_policy_document" "break_glass_assume_role" {
  count = var.enable_break_glass_role ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = var.break_glass_trusted_principal_arns
    }

    condition {
      test     = "Bool"
      variable = "aws:MultiFactorAuthPresent"
      values   = ["true"]
    }
  }
}

resource "aws_iam_role" "break_glass" {
  count = var.enable_break_glass_role ? 1 : 0

  name                 = "${var.name}-break-glass"
  description          = "Emergency administrator role requiring MFA and external monitoring"
  assume_role_policy   = data.aws_iam_policy_document.break_glass_assume_role[0].json
  permissions_boundary = var.permissions_boundary_arn
  max_session_duration = 3600

  tags = {
    AccessType = "emergency"
  }

  lifecycle {
    precondition {
      condition     = length(var.break_glass_trusted_principal_arns) > 0
      error_message = "At least one trusted principal is required when the break-glass role is enabled."
    }
  }
}

resource "aws_iam_role_policy_attachment" "break_glass" {
  count = var.enable_break_glass_role ? 1 : 0

  role       = aws_iam_role.break_glass[0].name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/AdministratorAccess"
}
