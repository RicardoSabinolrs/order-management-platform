variable "region" {
  description = "Regiao AWS."
  type        = string
  default     = "us-east-1"
}

variable "subnet_group_name" {
  description = "DB subnet group da VPC do ambiente."
  type        = string
}

variable "security_group_ids" {
  description = "Security groups que liberam acesso ao banco."
  type        = list(string)
}
