data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_region" "current" {}

locals {
  availability_zones = slice(data.aws_availability_zones.available.names, 0, var.az_count)
  vpc_prefix         = tonumber(split("/", var.cidr_block)[1])
  fixed_28_newbits   = 28 - local.vpc_prefix
  fixed_28_count     = pow(2, local.fixed_28_newbits)

  # The allocation works for /16-/22 VPCs and keeps every subnet at /28 or larger.
  # Pod subnets receive the largest blocks for VPC CNI secondary IP allocation.
  pod_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.cidr_block, 3, index)
  }
  node_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.cidr_block, 4, 8 + index)
  }
  ap_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.cidr_block, 5, 22 + index)
  }
  db_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.cidr_block, 6, 50 + index)
  }
  lb_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.cidr_block, 6, 53 + index)
  }
  tgw_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(
      var.cidr_block,
      local.fixed_28_newbits,
      local.fixed_28_count - (2 * var.az_count) + index,
    )
  }
  eks_cluster_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(
      var.cidr_block,
      local.fixed_28_newbits,
      local.fixed_28_count - var.az_count + index,
    )
  }
}

resource "aws_vpc" "this" {
  cidr_block           = var.cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = var.name
  }
}

resource "aws_subnet" "lb" {
  for_each = local.lb_subnets

  vpc_id                  = aws_vpc.this.id
  cidr_block              = each.value
  availability_zone       = each.key
  map_public_ip_on_launch = false

  tags = {
    Name                              = "${var.name}-lb-${each.key}"
    Tier                              = "load-balancer"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

resource "aws_subnet" "ap" {
  for_each = local.ap_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.name}-ap-${each.key}"
    Tier = "application"
  }
}

resource "aws_subnet" "db" {
  for_each = local.db_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.name}-db-${each.key}"
    Tier = "database"
  }
}

resource "aws_subnet" "node" {
  for_each = local.node_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.name}-node-${each.key}"
    Tier = "eks-node"
  }
}

resource "aws_subnet" "pod" {
  for_each = local.pod_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.name}-pod-${each.key}"
    Tier = "eks-pod"
  }
}

resource "aws_subnet" "tgw" {
  for_each = local.tgw_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.name}-tgw-${each.key}"
    Tier = "transit-gateway"
  }
}

resource "aws_subnet" "eks_cluster" {
  for_each = local.eks_cluster_subnets

  vpc_id            = aws_vpc.this.id
  cidr_block        = each.value
  availability_zone = each.key

  tags = {
    Name = "${var.name}-eks-cluster-${each.key}"
    Tier = "eks-cluster"
  }
}

resource "aws_route_table" "lb" {
  for_each = aws_subnet.lb
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-lb-${each.key}-rt" }
}

resource "aws_route_table" "ap" {
  for_each = aws_subnet.ap
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-ap-${each.key}-rt" }
}

resource "aws_route_table" "db" {
  for_each = aws_subnet.db
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-db-${each.key}-rt" }
}

resource "aws_route_table" "node" {
  for_each = aws_subnet.node
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-node-${each.key}-rt" }
}

resource "aws_route_table" "pod" {
  for_each = aws_subnet.pod
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-pod-${each.key}-rt" }
}

resource "aws_route_table" "tgw" {
  for_each = aws_subnet.tgw
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-tgw-${each.key}-rt" }
}

resource "aws_route_table" "eks_cluster" {
  for_each = aws_subnet.eks_cluster
  vpc_id   = aws_vpc.this.id
  tags     = { Name = "${var.name}-eks-cluster-${each.key}-rt" }
}

resource "aws_ec2_transit_gateway_vpc_attachment" "this" {
  subnet_ids         = values(aws_subnet.tgw)[*].id
  transit_gateway_id = var.transit_gateway_id
  vpc_id             = aws_vpc.this.id
  dns_support        = "enable"
  ipv6_support       = "disable"

  tags = {
    Name = "${var.name}-tgw"
  }
}

resource "aws_route" "lb_default" {
  for_each = aws_route_table.lb

  route_table_id         = each.value.id
  destination_cidr_block = var.centralized_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "ap_default" {
  for_each = aws_route_table.ap

  route_table_id         = each.value.id
  destination_cidr_block = var.centralized_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "node_default" {
  for_each = aws_route_table.node

  route_table_id         = each.value.id
  destination_cidr_block = var.centralized_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "pod_default" {
  for_each = aws_route_table.pod

  route_table_id         = each.value.id
  destination_cidr_block = var.centralized_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "eks_cluster_default" {
  for_each = aws_route_table.eks_cluster

  route_table_id         = each.value.id
  destination_cidr_block = var.centralized_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route_table_association" "lb" {
  for_each = aws_subnet.lb

  subnet_id      = each.value.id
  route_table_id = aws_route_table.lb[each.key].id
}

resource "aws_route_table_association" "ap" {
  for_each = aws_subnet.ap

  subnet_id      = each.value.id
  route_table_id = aws_route_table.ap[each.key].id
}

resource "aws_route_table_association" "db" {
  for_each = aws_subnet.db

  subnet_id      = each.value.id
  route_table_id = aws_route_table.db[each.key].id
}

resource "aws_route_table_association" "node" {
  for_each = aws_subnet.node

  subnet_id      = each.value.id
  route_table_id = aws_route_table.node[each.key].id
}

resource "aws_route_table_association" "pod" {
  for_each = aws_subnet.pod

  subnet_id      = each.value.id
  route_table_id = aws_route_table.pod[each.key].id
}

resource "aws_route_table_association" "tgw" {
  for_each = aws_subnet.tgw

  subnet_id      = each.value.id
  route_table_id = aws_route_table.tgw[each.key].id
}

resource "aws_route_table_association" "eks_cluster" {
  for_each = aws_subnet.eks_cluster

  subnet_id      = each.value.id
  route_table_id = aws_route_table.eks_cluster[each.key].id
}

resource "aws_security_group" "interface_endpoints" {
  count = length(var.interface_endpoint_services) > 0 ? 1 : 0

  name_prefix = "${var.name}-vpce-"
  description = "HTTPS access to VPC interface endpoints"
  vpc_id      = aws_vpc.this.id

  ingress {
    description = "HTTPS from the VPC"
    protocol    = "tcp"
    from_port   = 443
    to_port     = 443
    cidr_blocks = [var.cidr_block]
  }

  egress {
    description = "Endpoint responses"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name}-vpce"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_endpoint" "interface" {
  for_each = toset(var.interface_endpoint_services)

  vpc_id              = aws_vpc.this.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.${each.key}"
  vpc_endpoint_type   = "Interface"
  private_dns_enabled = true
  subnet_ids          = values(aws_subnet.node)[*].id
  security_group_ids  = [aws_security_group.interface_endpoints[0].id]

  tags = {
    Name = "${var.name}-${each.key}-vpce"
  }
}

resource "aws_vpc_endpoint" "s3" {
  count = var.enable_s3_gateway_endpoint ? 1 : 0

  vpc_id            = aws_vpc.this.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids = concat(
    values(aws_route_table.ap)[*].id,
    values(aws_route_table.db)[*].id,
    values(aws_route_table.node)[*].id,
    values(aws_route_table.pod)[*].id,
  )

  tags = {
    Name = "${var.name}-s3-vpce"
  }
}
