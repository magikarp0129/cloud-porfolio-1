locals {
  managed_rule_groups = {
    common = {
      name     = "AWSManagedRulesCommonRuleSet"
      priority = 10
    }
    known_bad_inputs = {
      name     = "AWSManagedRulesKnownBadInputsRuleSet"
      priority = 20
    }
    ip_reputation = {
      name     = "AWSManagedRulesAmazonIpReputationList"
      priority = 30
    }
    sql_injection = {
      name     = "AWSManagedRulesSQLiRuleSet"
      priority = 40
    }
  }
}

resource "aws_wafv2_web_acl" "this" {
  name        = var.name
  description = "Enterprise managed-rule and rate-limit baseline"
  scope       = var.scope

  default_action {
    allow {}
  }

  rule {
    name     = "RateLimitBySourceIp"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        aggregate_key_type = "IP"
        limit              = var.rate_limit
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${var.name}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  dynamic "rule" {
    for_each = local.managed_rule_groups

    content {
      name     = rule.value.name
      priority = rule.value.priority

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          name        = rule.value.name
          vendor_name = "AWS"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${var.name}-${rule.key}"
        sampled_requests_enabled   = true
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = var.name
    sampled_requests_enabled   = true
  }
}

resource "aws_cloudwatch_log_group" "this" {
  name              = "aws-waf-logs-${var.name}"
  retention_in_days = var.log_retention_days
}

resource "aws_wafv2_web_acl_logging_configuration" "this" {
  log_destination_configs = [aws_cloudwatch_log_group.this.arn]
  resource_arn            = aws_wafv2_web_acl.this.arn

  redacted_fields {
    single_header {
      name = "authorization"
    }
  }
}

resource "aws_wafv2_web_acl_association" "this" {
  for_each = var.scope == "REGIONAL" ? var.resource_arns : []

  resource_arn = each.value
  web_acl_arn  = aws_wafv2_web_acl.this.arn
}
