data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  patch_baselines = {
    ubuntu = {
      operating_system = "UBUNTU"
      products         = ["Ubuntu20.04", "Ubuntu22.04", "Ubuntu24.04"]
    }
    redhat = {
      operating_system = "REDHAT_ENTERPRISE_LINUX"
      products         = ["RedhatEnterpriseLinux8.*", "RedhatEnterpriseLinux9.*"]
    }
    amazon_linux_2023 = {
      operating_system = "AMAZON_LINUX_2023"
      products         = ["AmazonLinux2023"]
    }
  }
}

resource "aws_backup_vault" "this" {
  name        = "${var.name}-daily"
  kms_key_arn = var.backup_kms_key_arn
}

resource "aws_backup_vault_lock_configuration" "this" {
  count = var.enable_backup_vault_lock ? 1 : 0

  backup_vault_name   = aws_backup_vault.this.name
  changeable_for_days = var.backup_vault_lock_changeable_days
  min_retention_days  = var.backup_retention_days
  max_retention_days  = var.backup_retention_days * 12
}

resource "aws_backup_plan" "daily" {
  name = "${var.name}-daily"

  rule {
    rule_name         = "daily"
    target_vault_name = aws_backup_vault.this.name
    schedule          = var.backup_schedule
    start_window      = 60
    completion_window = 360

    lifecycle {
      delete_after = var.backup_retention_days
    }

    recovery_point_tags = {
      BackupPolicy = "daily"
      Environment  = var.environment
      ManagedBy    = "terraform"
    }
  }
}

data "aws_iam_policy_document" "backup_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["backup.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "backup" {
  name               = "${var.name}-backup"
  assume_role_policy = data.aws_iam_policy_document.backup_assume_role.json
}

resource "aws_iam_role_policy_attachment" "backup" {
  role       = aws_iam_role.backup.name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSBackupServiceRolePolicyForBackup"
}

resource "aws_backup_selection" "daily" {
  iam_role_arn = aws_iam_role.backup.arn
  name         = "${var.name}-daily-tag-selection"
  plan_id      = aws_backup_plan.daily.id

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "BackupPolicy"
    value = "daily"
  }

  selection_tag {
    type  = "STRINGEQUALS"
    key   = "Environment"
    value = var.environment
  }
}

data "archive_file" "scheduler" {
  count = var.enable_instance_scheduler ? 1 : 0

  type        = "zip"
  source_file = "${path.module}/src/scheduler.py"
  output_path = "${path.module}/scheduler.zip"
}

data "aws_iam_policy_document" "lambda_assume_role" {
  count = var.enable_instance_scheduler ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "scheduler_lambda" {
  count = var.enable_instance_scheduler ? 1 : 0

  name               = "${var.name}-instance-scheduler"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role[0].json
}

data "aws_iam_policy_document" "scheduler_lambda" {
  count = var.enable_instance_scheduler ? 1 : 0

  statement {
    sid    = "DiscoverTaggedResources"
    effect = "Allow"
    actions = [
      "ec2:DescribeInstances",
      "rds:DescribeDBClusters",
      "rds:DescribeDBInstances",
      "rds:ListTagsForResource",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "OperateEC2"
    effect = "Allow"
    actions = [
      "ec2:StartInstances",
      "ec2:StopInstances",
    ]
    resources = ["arn:${data.aws_partition.current.partition}:ec2:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:instance/*"]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Schedule"
      values   = ["office-hours"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Environment"
      values   = [var.environment]
    }
  }

  statement {
    sid    = "OperateRDS"
    effect = "Allow"
    actions = [
      "rds:StartDBCluster",
      "rds:StartDBInstance",
      "rds:StopDBCluster",
      "rds:StopDBInstance",
    ]
    resources = [
      "arn:${data.aws_partition.current.partition}:rds:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:cluster:*",
      "arn:${data.aws_partition.current.partition}:rds:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:db:*",
    ]

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Schedule"
      values   = ["office-hours"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:ResourceTag/Environment"
      values   = [var.environment]
    }
  }
}

resource "aws_iam_role_policy" "scheduler_lambda" {
  count = var.enable_instance_scheduler ? 1 : 0

  name   = "${var.name}-instance-scheduler"
  role   = aws_iam_role.scheduler_lambda[0].id
  policy = data.aws_iam_policy_document.scheduler_lambda[0].json
}

resource "aws_iam_role_policy_attachment" "lambda_basic" {
  count = var.enable_instance_scheduler ? 1 : 0

  role       = aws_iam_role.scheduler_lambda[0].name
  policy_arn = "arn:${data.aws_partition.current.partition}:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "scheduler" {
  count = var.enable_instance_scheduler ? 1 : 0

  function_name    = "${var.name}-instance-scheduler"
  description      = "Starts and stops tagged non-production EC2 and RDS resources"
  role             = aws_iam_role.scheduler_lambda[0].arn
  handler          = "scheduler.handler"
  runtime          = "python3.12"
  filename         = data.archive_file.scheduler[0].output_path
  source_code_hash = data.archive_file.scheduler[0].output_base64sha256
  timeout          = 120

  environment {
    variables = {
      TARGET_ENVIRONMENT = var.environment
      SCHEDULE_TAG_VALUE = "office-hours"
      DRY_RUN            = tostring(var.scheduler_dry_run)
    }
  }

  tracing_config {
    mode = "Active"
  }

  lifecycle {
    precondition {
      condition     = var.environment != "prod"
      error_message = "The instance scheduler cannot be enabled for prod."
    }
  }
}

resource "aws_cloudwatch_log_group" "scheduler" {
  count = var.enable_instance_scheduler ? 1 : 0

  name              = "/aws/lambda/${aws_lambda_function.scheduler[0].function_name}"
  retention_in_days = var.lambda_log_retention_days
}

data "aws_iam_policy_document" "scheduler_assume_role" {
  count = var.enable_instance_scheduler ? 1 : 0

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["scheduler.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "eventbridge_scheduler" {
  count = var.enable_instance_scheduler ? 1 : 0

  name               = "${var.name}-eventbridge-scheduler"
  assume_role_policy = data.aws_iam_policy_document.scheduler_assume_role[0].json
}

data "aws_iam_policy_document" "eventbridge_scheduler" {
  count = var.enable_instance_scheduler ? 1 : 0

  statement {
    effect    = "Allow"
    actions   = ["lambda:InvokeFunction"]
    resources = [aws_lambda_function.scheduler[0].arn]
  }
}

resource "aws_iam_role_policy" "eventbridge_scheduler" {
  count = var.enable_instance_scheduler ? 1 : 0

  name   = "${var.name}-invoke-scheduler"
  role   = aws_iam_role.eventbridge_scheduler[0].id
  policy = data.aws_iam_policy_document.eventbridge_scheduler[0].json
}

resource "aws_scheduler_schedule_group" "office_hours" {
  count = var.enable_instance_scheduler ? 1 : 0

  name = "${var.name}-office-hours"
}

resource "aws_scheduler_schedule" "office_hours" {
  for_each = var.enable_instance_scheduler ? {
    start = var.weekday_start_schedule
    stop  = var.weekday_stop_schedule
  } : {}

  name                         = "${var.name}-${each.key}"
  group_name                   = aws_scheduler_schedule_group.office_hours[0].name
  schedule_expression          = each.value
  schedule_expression_timezone = var.schedule_timezone
  state                        = "ENABLED"

  flexible_time_window {
    mode = "OFF"
  }

  target {
    arn      = aws_lambda_function.scheduler[0].arn
    role_arn = aws_iam_role.eventbridge_scheduler[0].arn
    input    = jsonencode({ action = each.key })

    retry_policy {
      maximum_event_age_in_seconds = 3600
      maximum_retry_attempts       = 2
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "scheduler_errors" {
  count = var.enable_instance_scheduler ? 1 : 0

  alarm_name          = "${var.name}-instance-scheduler-errors"
  alarm_description   = "Instance scheduler Lambda invocation failed."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.scheduler[0].function_name }
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  treat_missing_data  = "notBreaching"
  alarm_actions       = [var.alarm_topic_arn]
}

resource "aws_ssm_patch_baseline" "this" {
  for_each = local.patch_baselines

  name                              = "${var.name}-${replace(each.key, "_", "-")}"
  description                       = "Security patch baseline for ${each.value.operating_system}"
  operating_system                  = each.value.operating_system
  approved_patches_compliance_level = "CRITICAL"
  rejected_patches_action           = "BLOCK"

  approval_rule {
    approve_after_days  = var.patch_approval_days
    compliance_level    = "CRITICAL"
    enable_non_security = false

    patch_filter {
      key    = "CLASSIFICATION"
      values = ["Security", "SecurityUpdates"]
    }

    patch_filter {
      key    = "PRODUCT"
      values = each.value.products
    }
  }
}

resource "aws_ssm_patch_group" "this" {
  for_each = aws_ssm_patch_baseline.this

  baseline_id = each.value.id
  patch_group = "${var.environment}-${each.key}"
}

resource "aws_inspector2_enabler" "this" {
  count = var.enable_inspector ? 1 : 0

  account_ids    = [data.aws_caller_identity.current.account_id]
  resource_types = ["EC2", "ECR", "LAMBDA", "LAMBDA_CODE"]
}
