# ---------------------------------------------------------------------------
# Order Management Platform
#
#   make                 lista os alvos
#   make bootstrap       prepara a maquina
#   make dev             backend + frontend juntos (banco no Docker)
#   make dev-backend     so o backend        make dev-frontend   so o frontend
#   make up              tudo no Docker Compose
#   make minikube-up     tudo em um Kubernetes local
# ---------------------------------------------------------------------------
API_DIR    := apps/api
WEB_DIR    := apps/web
COMPOSE    := docker compose
MINIKUBE   := infra/minikube
IMAGE_TAG  ?= local

.DEFAULT_GOAL := help
.PHONY: help bootstrap env \
		dev dev-backend dev-frontend backend frontend seed migrate revision db-up db-down db-shell \
		test test-unit test-integration test-backend test-frontend lint lint-backend lint-frontend \
		fmt typecheck check check-backend check-frontend \
		up up-backend up-frontend down restart logs ps shell-api \
		docker-build docker-build-api docker-build-web docker-clean \
		minikube-up minikube-down minikube-delete minikube-deploy minikube-images \
		minikube-observability minikube-status minikube-logs minikube-dashboard \
		helm-lint helm-template openapi clean

help: ## Lista os alvos disponiveis
	@awk 'BEGIN {FS = ":.*?## "} \
		/^# -----/ {next} \
		/^##@/ {printf "\n\033[1m%s\033[0m\n", substr($$0, 5); next} \
		/^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo

##@ Preparacao
bootstrap: env ## Instala as dependencias do backend e do frontend
	cd $(API_DIR) && uv sync --all-extras
	pnpm install

env: ## Cria o .env a partir do exemplo, se ainda nao existir
	@test -f .env || (cp .env.example .env && echo "  .env criado a partir de .env.example")

##@ Desenvolvimento
dev: db-up migrate ## Backend + frontend juntos (Ctrl-C derruba os dois)
	@echo "  API      http://localhost:8000/docs"
	@echo "  Frontend http://localhost:5173"
	@trap 'kill 0' EXIT INT TERM; \
		(cd $(API_DIR) && uv run uvicorn main:app --reload --port 8000) & \
		VITE_USE_MOCKS=false pnpm --filter @oms/web dev & \
		wait

dev-backend: db-up migrate backend ## So o backend (sobe o banco antes)

dev-frontend: ## So o frontend, com a API mocada pelo MSW
	VITE_USE_MOCKS=true pnpm --filter @oms/web dev

backend: ## API com reload em http://localhost:8000 (exige banco no ar)
	cd $(API_DIR) && uv run uvicorn main:app --reload --port 8000

frontend: ## Frontend em http://localhost:5173, apontando para a API real
	VITE_USE_MOCKS=false pnpm --filter @oms/web dev

seed: ## Popula o banco com catalogo e pedidos de demonstracao
	cd $(API_DIR) && uv run python scripts/seed.py

openapi: ## Exporta o contrato OpenAPI para openapi.json
	cd $(API_DIR) && uv run python -c "import json, main; print(json.dumps(main.create_app().openapi(), indent=2, ensure_ascii=False))" > openapi.json
	@echo "  apps/api/openapi.json atualizado"

##@ Banco de dados
db-up: env ## Sobe apenas o Postgres
	$(COMPOSE) up -d postgres
	@$(COMPOSE) exec -T postgres sh -c 'until pg_isready -U $${POSTGRES_USER:-order_management} >/dev/null 2>&1; do sleep 1; done'

db-down: ## Derruba o Postgres
	$(COMPOSE) stop postgres

db-shell: ## Abre o psql
	$(COMPOSE) exec postgres psql -U order_management -d order_management

migrate: ## Aplica as migrations ate a HEAD
	cd $(API_DIR) && uv run alembic upgrade head

revision: ## Gera migration por autogenerate (make revision m="mensagem")
	cd $(API_DIR) && uv run alembic revision --autogenerate -m "$(m)"

##@ Qualidade
check: check-backend check-frontend ## Portao completo (o mesmo do CI)

check-backend: lint-backend ## Lint, tipos e testes do backend
	cd $(API_DIR) && uv run mypy src
	cd $(API_DIR) && uv run pytest -q

check-frontend: lint-frontend ## Lint, tipos e testes do frontend
	pnpm typecheck
	pnpm test

test: test-backend test-frontend ## Todos os testes

test-backend: ## Testes do backend (unitarios + integracao)
	cd $(API_DIR) && uv run pytest -q

test-unit: ## Testes unitarios (sem I/O, nao exigem banco)
	cd $(API_DIR) && uv run pytest tests/unit -q

test-integration: db-up migrate ## Testes de integracao (sobe o Postgres antes)
	cd $(API_DIR) && uv run pytest tests/integration -q

test-frontend: ## Testes do frontend
	pnpm test

lint: lint-backend lint-frontend ## Lint dos dois lados

lint-backend: ## Lint e formatacao do backend
	cd $(API_DIR) && uv run ruff check .
	cd $(API_DIR) && uv run ruff format --check .

lint-frontend: ## Lint do frontend
	pnpm lint

typecheck: ## Checagem estatica de tipos nos dois lados
	cd $(API_DIR) && uv run mypy src
	pnpm typecheck

fmt: ## Formata o backend
	cd $(API_DIR) && uv run ruff format . && uv run ruff check --fix .

##@ Docker Compose
up: env docker-build ## Sobe a stack completa (app + observabilidade)
	$(COMPOSE) up -d
	@echo
	@echo "  Frontend   http://localhost:5173"
	@echo "  API        http://localhost:8000/docs"
	@echo "  Prometheus http://localhost:9090"
	@echo "  Grafana    http://localhost:3000  (admin/admin)"
	@echo
	@echo "  Rode 'make seed' para popular o banco."

up-backend: env docker-build-api ## Sobe so Postgres + API
	$(COMPOSE) up -d postgres api

up-frontend: env docker-build-web ## Sobe so o frontend
	$(COMPOSE) up -d web

down: ## Derruba a stack
	$(COMPOSE) down --remove-orphans

restart: down up ## Recria a stack do zero

logs: ## Acompanha os logs (make logs s=api para um servico)
	$(COMPOSE) logs -f $(s)

ps: ## Estado dos servicos
	$(COMPOSE) ps

shell-api: ## Shell no container da API
	$(COMPOSE) exec api /bin/sh

##@ Imagens Docker
docker-build: docker-build-api docker-build-web ## Constroi as duas imagens

docker-build-api: ## Constroi a imagem da API
	docker build -t order-management-api:$(IMAGE_TAG) $(API_DIR)

docker-build-web: ## Constroi a imagem do frontend
	docker build -t order-management-web:$(IMAGE_TAG) -f $(WEB_DIR)/Dockerfile .

docker-clean: ## Remove containers, volumes e imagens do projeto
	$(COMPOSE) down -v --remove-orphans --rmi local

##@ Kubernetes local (Minikube)
minikube-up: ## Sobe cluster, Postgres e aplicacao
	$(MINIKUBE)/bootstrap.sh

minikube-observability: ## Sobe tambem Prometheus, Grafana e Loki no cluster
	WITH_OBSERVABILITY=1 $(MINIKUBE)/bootstrap.sh

minikube-images: ## Reconstroi as imagens dentro do daemon do Minikube
	@eval $$(minikube -p order-management docker-env) && \
		docker build -t order-management-api:$(IMAGE_TAG) $(API_DIR) && \
		docker build -t order-management-web:$(IMAGE_TAG) -f $(WEB_DIR)/Dockerfile .

minikube-deploy: minikube-images ## Reaplica o chart sem recriar o cluster
	helm upgrade --install order-management infra/helm/order-management \
		--namespace order-management --create-namespace \
		--values infra/helm/order-management/values.yaml \
		--values infra/helm/order-management/values-local.yaml \
		--set image.tag=$(IMAGE_TAG) --wait

minikube-status: ## Estado dos pods
	kubectl -n order-management get pods,svc,ingress

minikube-logs: ## Logs da API no cluster
	kubectl -n order-management logs -l app.kubernetes.io/component=api -f --tail=100

minikube-dashboard: ## Abre o dashboard do Kubernetes
	minikube dashboard --profile order-management

minikube-down: ## Remove a aplicacao, mantendo o cluster
	$(MINIKUBE)/teardown.sh

minikube-delete: ## Apaga o cluster inteiro
	DELETE_CLUSTER=1 $(MINIKUBE)/teardown.sh

##@ Helm
helm-lint: ## Valida o chart
	helm lint infra/helm/order-management --set image.tag=$(IMAGE_TAG)

helm-template: ## Renderiza um ambiente (make helm-template env=staging)
	helm template order-management infra/helm/order-management \
		--values infra/helm/order-management/values.yaml \
		--values infra/helm/order-management/values-$(or $(env),local).yaml \
		--set image.tag=$(IMAGE_TAG)

##@ Manutencao
clean: ## Remove caches e artefatos de build
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	rm -rf $(API_DIR)/.pytest_cache $(API_DIR)/.mypy_cache $(API_DIR)/.ruff_cache
	rm -rf $(WEB_DIR)/dist $(WEB_DIR)/node_modules/.vite
