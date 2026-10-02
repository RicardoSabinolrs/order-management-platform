# Postgres gerenciado da plataforma.
#
# A senha e gerada aqui e guardada no Secrets Manager; o External Secrets
# Operator a projeta como Secret do Kubernetes, que o chart Helm consome.
# Ela nunca transita por values.yaml nem pelo pipeline.

terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

resource "random_password" "database" {
  length  = 32
  special = true
  # Caracteres que quebram DSNs em URL.
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_instance" "this" {
  identifier     = "${var.name_prefix}-postgres"
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_encrypted     = true

  db_name  = var.database_name
  username = var.database_user
  password = random_password.database.result

  multi_az                = var.multi_az
  backup_retention_period = var.backup_retention_days
  deletion_protection     = var.deletion_protection
  skip_final_snapshot     = !var.deletion_protection

  db_subnet_group_name   = var.subnet_group_name
  vpc_security_group_ids = var.security_group_ids

  performance_insights_enabled = true
  auto_minor_version_upgrade   = true

  tags = var.tags
}

resource "aws_secretsmanager_secret" "database" {
  name = "${var.name_prefix}/database"
  tags = var.tags
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    host     = aws_db_instance.this.address
    port     = aws_db_instance.this.port
    dbname   = var.database_name
    username = var.database_user
    password = random_password.database.result
  })
}
