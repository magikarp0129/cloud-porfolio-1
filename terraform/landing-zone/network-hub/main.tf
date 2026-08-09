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
    tags = {
      Environment = "landing-zone"
      Owner       = "network-team"
      ManagedBy   = "terraform"
      Component   = "network-hub"
    }
  }
}

module "transit_gateway" {
  source = "../../modules/transit-gateway-hub"

  name            = "enterprise-apne2-tgw"
  description     = "Enterprise landing-zone hub for service VPCs"
  amazon_side_asn = 64520
  ram_principals  = var.ram_principals

  tags = {
    CostCenter = "cloud-platform"
  }
}
