# Terraform

Estado atual: **esqueleto**. A estrutura e os contratos dos modulos estao
definidos, mas nenhum recurso foi aplicado em nuvem ainda - nao ha backend
remoto configurado nem credenciais.

```
modules/database/       RDS Postgres + secret da senha
environments/staging/   composicao do ambiente de staging
environments/production/
```

Antes do primeiro `apply`:

1. Criar o bucket de state e a tabela de lock, e preencher o bloco `backend`.
2. Definir as variaveis de cada ambiente (`terraform.tfvars`, fora do git).
3. `terraform init && terraform plan` - o plan e revisado em PR antes do apply.
