data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}

resource "aws_sns_topic" "alarms" {
  name              = "${var.name}-alarms"
  kms_master_key_id = var.kms_key_arn

  tags = {
    Name = "${var.name}-alarms"
  }
}

data "aws_iam_policy_document" "alarm_topic" {
  statement {
    sid       = "AccountAdministration"
    effect    = "Allow"
    actions   = ["SNS:*"]
    resources = [aws_sns_topic.alarms.arn]

    principals {
      type        = "AWS"
      identifiers = ["arn:${data.aws_partition.current.partition}:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }

  statement {
    sid       = "AllowAWSAlertPublishers"
    effect    = "Allow"
    actions   = ["SNS:Publish"]
    resources = [aws_sns_topic.alarms.arn]

    principals {
      type        = "Service"
      identifiers = ["budgets.amazonaws.com", "cloudwatch.amazonaws.com", "costalerts.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_sns_topic_policy" "alarms" {
  arn    = aws_sns_topic.alarms.arn
  policy = data.aws_iam_policy_document.alarm_topic.json
}

resource "aws_sns_topic_subscription" "email" {
  for_each = var.alarm_email_addresses

  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = each.value
}

resource "aws_cloudwatch_log_group" "vpc_flow_logs" {
  name              = "/aws/vpc/${var.name}/flow-logs"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = {
    Name      = "${var.name}-vpc-flow-logs"
    DataClass = "internal"
  }
}

data "aws_iam_policy_document" "flow_logs_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }

    condition {
      test     = "StringEquals"
      variable = "aws:SourceAccount"
      values   = [data.aws_caller_identity.current.account_id]
    }
  }
}

resource "aws_iam_role" "flow_logs" {
  name               = "${var.name}-vpc-flow-logs"
  assume_role_policy = data.aws_iam_policy_document.flow_logs_assume_role.json
}

data "aws_iam_policy_document" "flow_logs" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.vpc_flow_logs.arn}:*"]
  }
}

resource "aws_iam_role_policy" "flow_logs" {
  name   = "${var.name}-vpc-flow-logs"
  role   = aws_iam_role.flow_logs.id
  policy = data.aws_iam_policy_document.flow_logs.json
}

resource "aws_flow_log" "this" {
  iam_role_arn             = aws_iam_role.flow_logs.arn
  log_destination          = aws_cloudwatch_log_group.vpc_flow_logs.arn
  log_destination_type     = "cloud-watch-logs"
  traffic_type             = "ALL"
  vpc_id                   = var.vpc_id
  max_aggregation_interval = 60

  tags = {
    Name = "${var.name}-vpc-flow-logs"
  }
}

resource "aws_cloudwatch_log_metric_filter" "rejected_flows" {
  name           = "${var.name}-rejected-flows"
  pattern        = "[version, account_id, interface_id, srcaddr, dstaddr, srcport, dstport, protocol, packets, bytes, start, end, action = REJECT, log_status]"
  log_group_name = aws_cloudwatch_log_group.vpc_flow_logs.name

  metric_transformation {
    name      = "RejectedFlows"
    namespace = "EnterprisePortfolio/Network"
    value     = "1"
  }
}

resource "aws_cloudwatch_metric_alarm" "rejected_flows" {
  alarm_name          = "${var.name}-rejected-network-flows"
  alarm_description   = "VPC rejected flow count exceeded the environment threshold."
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = aws_cloudwatch_log_metric_filter.rejected_flows.metric_transformation[0].name
  namespace           = aws_cloudwatch_log_metric_filter.rejected_flows.metric_transformation[0].namespace
  period              = 300
  statistic           = "Sum"
  threshold           = var.rejected_flow_threshold
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alarms.arn]
  ok_actions          = [aws_sns_topic.alarms.arn]

  tags = {
    Severity = "warning"
  }
}

resource "aws_cloudwatch_dashboard" "platform" {
  dashboard_name = "${var.name}-platform"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Rejected VPC Flows"
          region = data.aws_region.current.name
          stat   = "Sum"
          period = 300
          metrics = [
            ["EnterprisePortfolio/Network", "RejectedFlows"]
          ]
        }
      },
      {
        type   = "log"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Top Rejected Destinations"
          region = data.aws_region.current.name
          view   = "table"
          query  = "SOURCE '${aws_cloudwatch_log_group.vpc_flow_logs.name}' | fields dstAddr, dstPort, action | filter action = 'REJECT' | stats count(*) as rejects by dstAddr, dstPort | sort rejects desc | limit 20"
        }
      }
    ]
  })
}

data "aws_region" "current" {}
