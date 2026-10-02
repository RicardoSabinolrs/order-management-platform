terraform {
  required_version = ">= 1.9"

  # Preencher antes do primeiro init - state local nao serve para infra
  # compartilhada.
  # backend "s3" {
  #   bucket       = "sabino-labs-tfstate"
  #   key          = "order-management/staging.tfstate"
  #   region       = "us-east-1"
  #   use_lockfile = true
  #   encrypt      = true
  # }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = local.tags
  }
}

locals {
  environment = "staging"

  tags = {
    Project     = "order-management"
    Environment = local.environment
    ManagedBy   = "terraform"
  }
}

module "database" {
  source = "../../modules/database"

  name_prefix           = "order-management-${local.environment}"
  instance_class        = "db.t4g.micro"
  multi_az              = false
  deletion_protection   = false
  backup_retention_days = 3

  subnet_group_name  = var.subnet_group_name
  security_group_ids = var.security_group_ids

  tags = local.tags
}
