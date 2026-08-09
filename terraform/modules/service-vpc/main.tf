data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  available_az_by_id = zipmap(
    data.aws_availability_zones.available.zone_ids,
    data.aws_availability_zones.available.names,
  )
  selected_az_ids = length(var.availability_zone_ids) > 0 ? var.availability_zone_ids : slice(
    data.aws_availability_zones.available.zone_ids,
    0,
    var.az_count,
  )
  availability_zones = [for zone_id in local.selected_az_ids : local.available_az_by_id[zone_id]]
  vpc_prefix         = tonumber(split("/", var.vpc_cidr)[1])
  fixed_28_newbits   = 28 - local.vpc_prefix
  fixed_28_count     = pow(2, local.fixed_28_newbits)

  # For the smallest supported /22 with three AZs, Pod=/25, Node=/26,
  # AP=/27 and LB/DB=/28. TGW and EKS cluster subnets stay fixed at /28.
  pod_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.vpc_cidr, 3, index)
  }
  node_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.vpc_cidr, 4, 8 + index)
  }
  ap_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.vpc_cidr, 5, 22 + index)
  }
  db_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.vpc_cidr, 6, 50 + index)
  }
  lb_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(var.vpc_cidr, 6, 53 + index)
  }
  tgw_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(
      var.vpc_cidr,
      local.fixed_28_newbits,
      local.fixed_28_count - (2 * var.az_count) + index,
    )
  }
  eks_cluster_subnets = {
    for index, az in local.availability_zones : az => cidrsubnet(
      var.vpc_cidr,
      local.fixed_28_newbits,
      local.fixed_28_count - var.az_count + index,
    )
  }

  db_enterprise_routes = {
    for pair in setproduct(local.availability_zones, var.enterprise_cidrs) :
    "${pair[0]}|${pair[1]}" => { az = pair[0], cidr = pair[1] }
  }

  common_tags = merge(var.tags, {
    Service         = var.service_name
    Environment     = var.environment
    WorkloadProfile = var.workload_profile
    ManagedBy       = "terraform"
  })
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(local.common_tags, { Name = var.name })
}

resource "aws_subnet" "lb" {
  for_each = local.lb_subnets

  vpc_id                  = aws_vpc.this.id
  availability_zone       = each.key
  cidr_block              = each.value
  map_public_ip_on_launch = false
  tags = merge(local.common_tags, {
    Name                              = "${var.name}-lb-${each.key}"
    Tier                              = "load-balancer"
    "kubernetes.io/role/internal-elb" = "1"
  })
}

resource "aws_subnet" "ap" {
  for_each = local.ap_subnets

  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  cidr_block        = each.value
  tags              = merge(local.common_tags, { Name = "${var.name}-ap-${each.key}", Tier = "application" })
}

resource "aws_subnet" "db" {
  for_each = local.db_subnets

  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  cidr_block        = each.value
  tags              = merge(local.common_tags, { Name = "${var.name}-db-${each.key}", Tier = "database" })
}

resource "aws_subnet" "node" {
  for_each = local.node_subnets

  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  cidr_block        = each.value
  tags              = merge(local.common_tags, { Name = "${var.name}-node-${each.key}", Tier = "eks-node" })
}

resource "aws_subnet" "pod" {
  for_each = local.pod_subnets

  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  cidr_block        = each.value
  tags              = merge(local.common_tags, { Name = "${var.name}-pod-${each.key}", Tier = "eks-pod" })
}

resource "aws_subnet" "tgw" {
  for_each = local.tgw_subnets

  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  cidr_block        = each.value
  tags              = merge(local.common_tags, { Name = "${var.name}-tgw-${each.key}", Tier = "transit-gateway" })
}

resource "aws_subnet" "eks_cluster" {
  for_each = local.eks_cluster_subnets

  vpc_id            = aws_vpc.this.id
  availability_zone = each.key
  cidr_block        = each.value
  tags              = merge(local.common_tags, { Name = "${var.name}-eks-cluster-${each.key}", Tier = "eks-cluster" })
}

resource "aws_route_table" "lb" {
  for_each = aws_subnet.lb
  vpc_id   = aws_vpc.this.id
  tags     = merge(local.common_tags, { Name = "${var.name}-lb-${each.key}" })
}

resource "aws_route_table" "ap" {
  for_each = aws_subnet.ap
  vpc_id   = aws_vpc.this.id
  tags     = merge(local.common_tags, { Name = "${var.name}-ap-${each.key}" })
}

resource "aws_route_table" "db" {
  for_each = aws_subnet.db
  vpc_id   = aws_vpc.this.id
  tags     = merge(local.common_tags, { Name = "${var.name}-db-${each.key}" })
}

resource "aws_route_table" "node" {
  for_each = aws_subnet.node
  vpc_id   = aws_vpc.this.id
  tags     = merge(local.common_tags, { Name = "${var.name}-node-${each.key}" })
}

resource "aws_route_table" "pod" {
  for_each = aws_subnet.pod
  vpc_id   = aws_vpc.this.id
  tags     = merge(local.common_tags, { Name = "${var.name}-pod-${each.key}" })
}

resource "aws_route_table" "tgw" {
  for_each = aws_subnet.tgw
  vpc_id   = aws_vpc.this.id
  tags     = merge(local.common_tags, { Name = "${var.name}-tgw-${each.key}" })
}

resource "aws_route_table" "eks_cluster" {
  for_each = aws_subnet.eks_cluster
  vpc_id   = aws_vpc.this.id
  tags     = merge(local.common_tags, { Name = "${var.name}-eks-cluster-${each.key}" })
}

resource "aws_ec2_transit_gateway_vpc_attachment" "this" {
  subnet_ids         = values(aws_subnet.tgw)[*].id
  transit_gateway_id = var.transit_gateway_id
  vpc_id             = aws_vpc.this.id
  dns_support        = "enable"
  ipv6_support       = "disable"

  tags = merge(local.common_tags, { Name = "${var.name}-tgw" })
}

resource "aws_route" "lb_default" {
  for_each = aws_route_table.lb

  route_table_id         = each.value.id
  destination_cidr_block = var.landing_zone_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "ap_default" {
  for_each = aws_route_table.ap

  route_table_id         = each.value.id
  destination_cidr_block = var.landing_zone_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "node_default" {
  for_each = aws_route_table.node

  route_table_id         = each.value.id
  destination_cidr_block = var.landing_zone_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "pod_default" {
  for_each = aws_route_table.pod

  route_table_id         = each.value.id
  destination_cidr_block = var.landing_zone_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "eks_cluster_default" {
  for_each = aws_route_table.eks_cluster

  route_table_id         = each.value.id
  destination_cidr_block = var.landing_zone_default_route_cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route" "db_enterprise" {
  for_each = local.db_enterprise_routes

  route_table_id         = aws_route_table.db[each.value.az].id
  destination_cidr_block = each.value.cidr
  transit_gateway_id     = var.transit_gateway_id
  depends_on             = [aws_ec2_transit_gateway_vpc_attachment.this]
}

resource "aws_route_table_association" "lb" {
  for_each       = aws_subnet.lb
  subnet_id      = each.value.id
  route_table_id = aws_route_table.lb[each.key].id
}

resource "aws_route_table_association" "ap" {
  for_each       = aws_subnet.ap
  subnet_id      = each.value.id
  route_table_id = aws_route_table.ap[each.key].id
}

resource "aws_route_table_association" "db" {
  for_each       = aws_subnet.db
  subnet_id      = each.value.id
  route_table_id = aws_route_table.db[each.key].id
}

resource "aws_route_table_association" "node" {
  for_each       = aws_subnet.node
  subnet_id      = each.value.id
  route_table_id = aws_route_table.node[each.key].id
}

resource "aws_route_table_association" "pod" {
  for_each       = aws_subnet.pod
  subnet_id      = each.value.id
  route_table_id = aws_route_table.pod[each.key].id
}

resource "aws_route_table_association" "tgw" {
  for_each       = aws_subnet.tgw
  subnet_id      = each.value.id
  route_table_id = aws_route_table.tgw[each.key].id
}

resource "aws_route_table_association" "eks_cluster" {
  for_each       = aws_subnet.eks_cluster
  subnet_id      = each.value.id
  route_table_id = aws_route_table.eks_cluster[each.key].id
}
