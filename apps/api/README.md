# Order Management API

Gestao de catalogo, estoque e pedidos. FastAPI com separacao em camadas e
regra de dependencia apontando para dentro.

## Estrutura

```
src/
├── main.py       fabrica da aplicacao e entrypoint ASGI
├── api/          endpoints, dependencias, middlewares, traducao de erros
│   ├── health.py   sondas (fora do prefixo versionado)
│   └── v1/         auth, dashboard, products, stock, orders
├── domain/       regra de negocio, sem framework
│   ├── model/      Product, StockItem, Order, Money, User
│   ├── schema/     contratos de entrada e saida (Pydantic)
│   ├── repository/ portas de persistencia (Protocol)
│   └── service/    TODA a logica de negocio
├── infra/        banco, logging, metricas, config, repositorios concretos
└── security/     Argon2id, JWT e dependencias de autenticacao
```

`domain/` nao pode importar `fastapi`, `sqlalchemy` nem `starlette` - o `ruff`
reprova.

## Regras que moram aqui

- Criar pedido **reserva** estoque; cancelar **libera**; enviar **baixa**.
- Saldo disponivel = em maos - reservado.
- Transicao de status segue `ALLOWED_TRANSITIONS`; qualquer outra da 409.
- Preco do item vem do catalogo no momento da venda, nunca do payload.
- Produto com reserva nao pode ser excluido; pedido so depois de cancelado.

## Comandos

```bash
uv sync --all-extras
uv run uvicorn main:app --reload        # http://localhost:8000/docs
uv run pytest tests/unit -q             # nao precisa de banco
uv run pytest tests/integration -q      # exige Postgres no ar
uv run ruff check . && uv run mypy src
uv run alembic upgrade head
uv run python scripts/seed.py           # dados de demonstracao
```

Da raiz do monorepo: `make dev-backend`, `make test-unit`, `make check-backend`,
`make migrate`, `make seed`.

## Migrations

```bash
make revision m="adiciona tabela de fornecedores"
make migrate
```

Toda migration precisa de um `downgrade` funcional: o rollback do release
depende disso.
