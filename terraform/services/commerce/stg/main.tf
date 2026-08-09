terraform {
  required_version = ">= 1.6.0"
  required_providers { aws = { source = "hashicorp/aws", version = "~> 5.0" } }
  backend "s3" {}
}

variable "transit_gateway_id" { type = string }
variable "aws_region" {
  type    = string
  default = "ap-northeast-2"
}

provider "aws" { region = var.aws_region }

module "network" {
  source = "../../../modules/service-vpc"

  name                  = "commerce-stg"
  service_name          = "commerce"
  environment           = "stg"
  workload_profile      = "high-growth-eks-api"
  vpc_cidr              = "10.64.32.0/19"
  az_count              = 2
  availability_zone_ids = ["apne2-az1", "apne2-az2"]
  transit_gateway_id    = var.transit_gateway_id
}

output "service_network" {
  value = { vpc_id = module.network.vpc_id, vpc_cidr = module.network.vpc_cidr, attachment_id = module.network.transit_gateway_attachment_id, subnet_cidrs = module.network.subnet_cidrs }
}
