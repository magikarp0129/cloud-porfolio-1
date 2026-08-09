output "route_ids" {
  description = "Route resource IDs keyed by semantic route name."
  value       = { for key, route in aws_route.this : key => route.id }
}
