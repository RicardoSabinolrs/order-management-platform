output "database_endpoint" {
  description = "Endpoint do Postgres do ambiente."
  value       = module.database.endpoint
}

output "database_secret_arn" {
  description = "Secret com as credenciais, consumido pelo External Secrets."
  value       = module.database.secret_arn
}
