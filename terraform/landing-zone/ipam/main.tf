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
      Component   = "ipam"
    }
  }
}

locals {
  enterprise_cidr = "10.64.0.0/10"

  service_pools = {
    commerce = {
      cidr        = "10.64.0.0/13"
      min_netmask = 16
      max_netmask = 20
    }
    payments = {
      cidr        = "10.72.0.0/14"
      min_netmask = 18
      max_netmask = 22
    }
    analytics = {
      cidr        = "10.76.0.0/14"
      min_netmask = 16
      max_netmask = 20
    }
    customer-profile = {
      cidr        = "10.80.0.0/14"
      min_netmask = 19
      max_netmask = 22
    }
    internal-admin = {
      cidr        = "10.84.0.0/16"
      min_netmask = 20
      max_netmask = 22
    }
  }

  service_environment_cidrs = {
    commerce = {
      dev  = "10.64.0.0/20"
      stg  = "10.64.32.0/19"
      prod = "10.65.0.0/16"
    }
    payments = {
      dev  = "10.72.0.0/22"
      stg  = "10.72.8.0/21"
      prod = "10.73.0.0/18"
    }
    analytics = {
      dev  = "10.76.0.0/20"
      stg  = "10.76.64.0/18"
      prod = "10.77.0.0/16"
    }
    customer-profile = {
      dev  = "10.80.0.0/22"
      stg  = "10.80.8.0/21"
      prod = "10.81.0.0/19"
    }
    internal-admin = {
      dev  = "10.84.0.0/22"
      stg  = "10.84.4.0/22"
      prod = "10.84.16.0/20"
    }
  }
}

resource "aws_vpc_ipam" "this" {
  description = "Enterprise private IPv4 address management"
  tier        = var.ipam_tier

  operating_regions {
    region_name = var.aws_region
  }
}

resource "aws_vpc_ipam_pool" "regional" {
  address_family = "ipv4"
  description    = "Enterprise ap-northeast-2 private IPv4 pool"
  ipam_scope_id  = aws_vpc_ipam.this.private_default_scope_id
  locale         = var.aws_region
}

resource "aws_vpc_ipam_pool_cidr" "regional" {
  ipam_pool_id = aws_vpc_ipam_pool.regional.id
  cidr         = local.enterprise_cidr
}

resource "aws_vpc_ipam_pool" "service" {
  for_each = local.service_pools

  address_family                = "ipv4"
  allocation_min_netmask_length = each.value.min_netmask
  allocation_max_netmask_length = each.value.max_netmask
  description                   = "${each.key} service address pool"
  ipam_scope_id                 = aws_vpc_ipam.this.private_default_scope_id
  locale                        = var.aws_region
  source_ipam_pool_id           = aws_vpc_ipam_pool.regional.id

  allocation_resource_tags = {
    Service = each.key
  }

  depends_on = [aws_vpc_ipam_pool_cidr.regional]
}

resource "aws_vpc_ipam_pool_cidr" "service" {
  for_each = local.service_pools

  ipam_pool_id = aws_vpc_ipam_pool.service[each.key].id
  cidr         = each.value.cidr
}
