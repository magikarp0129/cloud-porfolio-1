variable "route_table_ids" {
  description = "Route table IDs keyed by stable logical names or availability zones."
  type        = map(string)
}

variable "routes" {
  description = "Additional routes keyed by semantic names. Exactly one destination and target must be set."
  type = map(object({
    route_table_key             = string
    destination_cidr_block      = optional(string)
    destination_ipv6_cidr_block = optional(string)
    destination_prefix_list_id  = optional(string)
    gateway_id                  = optional(string)
    nat_gateway_id              = optional(string)
    transit_gateway_id          = optional(string)
    vpc_peering_connection_id   = optional(string)
    network_interface_id        = optional(string)
    vpc_endpoint_id             = optional(string)
    egress_only_gateway_id      = optional(string)
  }))
  default = {}

  validation {
    condition = alltrue([
      for route in values(var.routes) : length(compact([
        route.destination_cidr_block,
        route.destination_ipv6_cidr_block,
        route.destination_prefix_list_id,
      ])) == 1
    ])
    error_message = "Each route must set exactly one destination."
  }

  validation {
    condition = alltrue([
      for route in values(var.routes) : length(compact([
        route.gateway_id,
        route.nat_gateway_id,
        route.transit_gateway_id,
        route.vpc_peering_connection_id,
        route.network_interface_id,
        route.vpc_endpoint_id,
        route.egress_only_gateway_id,
      ])) == 1
    ])
    error_message = "Each route must set exactly one target."
  }
}
