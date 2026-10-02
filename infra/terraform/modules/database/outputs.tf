output "endpoint" {
  description = "Endereco de conexao da instancia."
  value       = aws_db_instance.this.address
}

output "port" {
  description = "Porta de conexao."
  value       = aws_db_instance.this.port
}

output "secret_arn" {
  description = "ARN do secret com as credenciais (consumido pelo External Secrets)."
  value       = aws_secretsmanager_secret.database.arn
}
