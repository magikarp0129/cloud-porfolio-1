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
    Environment = "organization"
    Owner       = "platform-team"
    Service     = "cloud-portfolio"
    CostCenter  = "cloud-platform"
    ManagedBy   = "terraform"
  }

  organizational_units = {
    security = {
      name = "Security"
    }
    infrastructure = {
      name = "Infrastructure"
    }
    workloads = {
      name = "Workloads"
    }
    sandbox = {
      name = "Sandbox"
    }
    policy_staging = {
      name = "Policy-Staging"
    }
    workloads_dev = {
      name       = "Dev"
      parent_key = "workloads"
    }
    workloads_stg = {
      name       = "Stg"
      parent_key = "workloads"
    }
    workloads_prod = {
      name       = "Prod"
      parent_key = "workloads"
    }
  }
}

module "organization" {
  source = "../modules/organization"

  organizational_units = local.organizational_units
}

module "scp_policy" {
  source = "../modules/scp-policy"

  policies = {
    deny_leave_organization = {
      name        = "DenyLeaveOrganization"
      description = "Prevents member accounts from leaving the organization."
      content = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Sid      = "DenyLeaveOrganization"
            Effect   = "Deny"
            Action   = "organizations:LeaveOrganization"
            Resource = "*"
          }
        ]
      })
    }

    deny_disable_audit_services = {
      name        = "DenyDisableAuditServices"
      description = "Prevents disabling core audit and security services."
      content = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Sid    = "DenyDisableCloudTrailConfigGuardDuty"
            Effect = "Deny"
            Action = [
              "cloudtrail:StopLogging",
              "cloudtrail:DeleteTrail",
              "config:DeleteConfigurationRecorder",
              "config:StopConfigurationRecorder",
              "guardduty:DeleteDetector",
              "guardduty:UpdateDetector",
              "securityhub:DisableSecurityHub",
              "ec2:DeleteFlowLogs",
              "kms:DisableKey",
              "kms:ScheduleKeyDeletion"
            ]
            Resource = "*"
            Condition = {
              ArnNotLike = {
                "aws:PrincipalArn" = var.security_admin_role_arn_patterns
              }
            }
          }
        ]
      })
    }

    deny_unapproved_regions = {
      name        = "DenyUnapprovedRegions"
      description = "Restricts resource operations to approved regions."
      content = jsonencode({
        Version = "2012-10-17"
        Statement = [
          {
            Sid    = "DenyUnapprovedRegions"
            Effect = "Deny"
            NotAction = [
              "account:*",
              "acm:*",
              "aws-portal:*",
              "billing:*",
              "budgets:*",
              "ce:*",
              "cloudfront:*",
              "globalaccelerator:*",
              "health:*",
              "iam:*",
              "importexport:*",
              "networkmanager:*",
              "organizations:*",
              "route53:*",
              "route53domains:*",
              "shield:*",
              "support:*",
              "supportplans:*",
              "tag:*",
              "tax:*",
              "trustedadvisor:*",
              "waf:*"
            ]
            Resource = "*"
            Condition = {
              StringNotEquals = {
                "aws:RequestedRegion" = var.approved_regions
              }
            }
          }
        ]
      })
    }

    deny_delete_public_access_controls = {
      name        = "DenyDeletePublicAccessControls"
      description = "Prevents deletion of account and bucket public access controls."
      content = jsonencode({
        Version = "2012-10-17"
        Statement = [{
          Sid      = "DenyDeletePublicAccessControls"
          Effect   = "Deny"
          Action   = ["s3:DeleteAccountPublicAccessBlock", "s3:DeleteBucketPublicAccessBlock"]
          Resource = "*"
          Condition = {
            ArnNotLike = {
              "aws:PrincipalArn" = var.security_admin_role_arn_patterns
            }
          }
        }]
      })
    }

    enterprise_tag_policy = {
      name        = "EnterpriseTagPolicy"
      description = "Standardizes enterprise tag keys and controlled values."
      type        = "TAG_POLICY"
      content = jsonencode({
        tags = {
          Environment = {
            tag_key      = { "@@assign" = "Environment" }
            tag_value    = { "@@assign" = ["dev", "stg", "prod", "shared", "security", "sandbox"] }
            enforced_for = { "@@assign" = ["ec2:instance", "eks:cluster", "rds:db", "s3:bucket"] }
          }
          ManagedBy = {
            tag_key      = { "@@assign" = "ManagedBy" }
            tag_value    = { "@@assign" = ["terraform", "cloudformation", "manual-exception"] }
            enforced_for = { "@@assign" = ["ec2:instance", "eks:cluster", "rds:db", "s3:bucket"] }
          }
        }
      })
    }
  }

  attachments = {
    workloads_deny_disable_audit_services = {
      policy_key = "deny_disable_audit_services"
      target_id  = module.organization.organizational_unit_ids["workloads"]
    }
    workloads_deny_unapproved_regions = {
      policy_key = "deny_unapproved_regions"
      target_id  = module.organization.organizational_unit_ids["workloads"]
    }
    workloads_deny_leave_organization = {
      policy_key = "deny_leave_organization"
      target_id  = module.organization.organizational_unit_ids["workloads"]
    }
    infrastructure_deny_leave_organization = {
      policy_key = "deny_leave_organization"
      target_id  = module.organization.organizational_unit_ids["infrastructure"]
    }
    security_deny_leave_organization = {
      policy_key = "deny_leave_organization"
      target_id  = module.organization.organizational_unit_ids["security"]
    }
    sandbox_deny_leave_organization = {
      policy_key = "deny_leave_organization"
      target_id  = module.organization.organizational_unit_ids["sandbox"]
    }
    workloads_deny_delete_public_access_controls = {
      policy_key = "deny_delete_public_access_controls"
      target_id  = module.organization.organizational_unit_ids["workloads"]
    }
    workloads_enterprise_tag_policy = {
      policy_key = "enterprise_tag_policy"
      target_id  = module.organization.organizational_unit_ids["workloads"]
    }
    sandbox_enterprise_tag_policy = {
      policy_key = "enterprise_tag_policy"
      target_id  = module.organization.organizational_unit_ids["sandbox"]
    }
  }
}
