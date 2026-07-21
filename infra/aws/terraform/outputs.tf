output "name_prefix" {
  description = "Stable prefix future resources should use."
  value       = local.name_prefix
}

output "backend_url" {
  description = "Backend service URL after service resources are added."
  value       = null
}

output "frontend_url" {
  description = "Frontend URL after hosting resources are added."
  value       = null
}
