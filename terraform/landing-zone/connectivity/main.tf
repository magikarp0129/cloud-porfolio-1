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
      Component   = "tgw-routing"
    }
  }
}

module "routing" {
  source = "../../modules/transit-gateway-routing"

  route_table_ids                  = var.route_table_ids
  service_attachments              = var.service_attachments
  inspection_attachment_id         = var.inspection_attachment_id
  shared_services_attachment_id    = var.shared_services_attachment_id
  enable_inspection_default_routes = var.enable_inspection_default_routes
  allowed_routes                   = var.allowed_routes
}
