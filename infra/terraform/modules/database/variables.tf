variable "name_prefix" {
  description = "Prefixo dos recursos (ex.: order-management-staging)."
  type        = string
}

variable "engine_version" {
  description = "Versao do Postgres."
  type        = string
  default     = "17.4"
}

variable "instance_class" {
  description = "Classe da instancia RDS."
  type        = string
  default     = "db.t4g.micro"
}

variable "allocated_storage" {
  description = "Armazenamento inicial, em GB."
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Teto do autoscaling de armazenamento, em GB."
  type        = number
  default     = 100
}

variable "database_name" {
  description = "Nome do banco."
  type        = string
  default     = "order_management"
}

variable "database_user" {
  description = "Usuario administrador."
  type        = string
  default     = "order_management"
}

variable "multi_az" {
  description = "Habilita alta disponibilidade entre zonas."
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Retencao de backups automaticos, em dias."
  type        = number
  default     = 7
}

variable "deletion_protection" {
  description = "Impede destruicao acidental da instancia."
  type        = bool
  default     = true
}

variable "subnet_group_name" {
  description = "DB subnet group onde a instancia sobe."
  type        = string
}

variable "security_group_ids" {
  description = "Security groups aplicados a instancia."
  type        = list(string)
}

variable "tags" {
  description = "Tags aplicadas a todos os recursos."
  type        = map(string)
  default     = {}
}
