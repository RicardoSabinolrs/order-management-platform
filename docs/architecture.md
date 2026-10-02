# Arquitetura

## Por que separar em camadas

A regra que diz "um pedido so pode ser enviado depois de confirmado" e que
"enviar baixa o estoque reservado" vai sobreviver ao FastAPI, ao Postgres e ao
provedor de nuvem atual. A separacao em camadas existe para que trocar
qualquer um dos tres seja uma mudanca de adapter, nao uma reescrita.

O nucleo (`domain/`) nao importa framework algum. Isso e verificado
mecanicamente: o `ruff` bloqueia `import fastapi`, `import sqlalchemy` e
`import starlette` fora das camadas de adapter (`tool.ruff.lint.flake8-tidy-imports`
em `apps/api/pyproject.toml`). Nao e convencao de equipe - o CI reprova.

```
                    ┌──────────────────────────────┐
   HTTP, CLI   ───▶ │  api/       (adapter in)     │
   consumers        └──────────────┬───────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │  domain/service/             │  toda a regra de negocio
                    └──────────────┬───────────────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │  domain/model/               │  invariantes dos agregados
                    └──────────────▲───────────────┘
                                   │  implementa as portas
                    ┌──────────────┴───────────────┐
                    │  infra/     (adapter out)    │ ──▶ Postgres
                    └──────────────────────────────┘
```

| Camada     | O que vive ali                                   | Pode depender de              |
| ---------- | ------------------------------------------------ | ----------------------------- |
| `domain`   | agregados, schemas, portas, services             | nada                          |
| `infra`    | banco, logging, metricas, config, repositorios    | `domain`                      |
| `security` | hashing, JWT, dependencias de autenticacao        | `domain`, `infra`             |
| `api`      | routers, dependencias, middlewares, erros         | `domain`, `infra`, `security` |

## Endpoints magros

Um endpoint recebe apenas o service e devolve o que ele retorna:

```python
@router.post("/orders", response_model=OrderRead, status_code=201)
async def create_order(payload: OrderCreate, service: OrderServiceDep) -> OrderRead:
    return await service.create(payload)
```

Nenhuma regra, nenhum acesso a repositorio e nenhum `if` de negocio vive em
`api/`. O ganho pratico aparece nos testes: `tests/unit/test_order_service.py`
exercita a regra inteira com repositorios em memoria, em milissegundos e sem
banco. A camada HTTP e testada separadamente, so pelo que lhe cabe -
serializacao, status e traducao de erro.

## Onde mora cada decisao

**O modelo protege as proprias invariantes.** `StockItem.reserve()` recusa
reservar mais do que o disponivel; `Order.confirm()` recusa a transicao fora da
maquina de estados. E impossivel construir um `Order` sem itens ou um `Money`
negativo. O service orquestra, mas nao e ele quem garante a consistencia.

**Agregado e fronteira transacional.** Uma transacao escreve um agregado.
Produto, estoque e pedido sao agregados distintos: um ajuste de preco nao
disputa a mesma linha que uma baixa de estoque.

**A unidade de trabalho expoe os repositorios.** Criar um pedido grava o
pedido e reserva o estoque na mesma transacao, ou nao grava nada. Se a reserva
do segundo item falhar, a do primeiro e desfeita junto - nao existe estado
intermediario em que o pedido existe sem o estoque correspondente.

**Reserva usa `SELECT ... FOR UPDATE`.** Reservar e ler-decidir-escrever. Sem o
lock, duas transacoes leem o mesmo saldo e vendem a mesma unidade duas vezes.
`tests/integration/test_order_flow.py::test_reservas_concorrentes_nao_vendem_a_mesma_unidade`
dispara os dois pedidos em paralelo e exige que exatamente um passe.

**Dinheiro em centavos, sempre.** `0.1 + 0.2 != 0.3` em ponto flutuante
binario, e um centavo perdido por arredondamento vira divergencia contabil.
`Money` guarda inteiros e recusa misturar moedas.

**O preco vem do catalogo, nunca do payload.** Aceitar preco do cliente
permitiria comprar qualquer coisa por um centavo. O item do pedido copia SKU,
descricao e preco no momento da venda - mudanca de tabela depois nao reescreve
o historico.

**Erros de dominio sao parte do contrato.** O service levanta
`InsufficientStockError`, `InvalidStatusTransitionError`, `EntityNotFoundError`.
Somente `api/errors.py` conhece codigo HTTP, e o corpo segue o RFC 9457 com os
dados necessarios para agir:

```json
{
  "code": "insufficient_stock",
  "detail": "Estoque insuficiente para o SKU CAF-500: solicitado 5, disponivel 2.",
  "sku": "CAF-500", "requested": 5, "available": 2
}
```

**Excluir preserva o historico.** Produto com estoque reservado nao pode ser
excluido (desative-o); pedido so pode ser excluido depois de cancelado. A chave
estrangeira de `order_items.product_id` e `RESTRICT`: o banco tambem recusa.

**As invariantes estao no banco tambem.** `stock_items` tem `CHECK` para saldo
nao negativo e reserva menor ou igual ao saldo. Um script avulso ou uma
correcao manual nao conseguem corromper o estoque.

**Lock otimista nas escritas.** `version` no agregado e na tabela. Conflito
vira `ConcurrencyConflictError` -> HTTP 409.

## Configuracao e seguranca

Toda variavel de ambiente entra por `infra/config/settings.py`. Nenhum outro
modulo le `os.environ`. A configuracao se recusa a subir em staging ou
producao com a chave de assinatura ou a senha de demonstracao do repositorio -
o processo falha no start em vez de rodar inseguro.

Senhas usam Argon2id (recomendacao do OWASP; o hash embute sal e parametros de
custo). Tokens sao JWT com emissor e expiracao validados. Login responde a
mesma mensagem para e-mail desconhecido e senha errada: distinguir os dois
entregaria a lista de e-mails validos a quem estivesse sondando.

Hoje ha um unico operador, definido por configuracao
(`infra/repository/user.py`). Quando existir cadastro de usuarios, basta trocar
essa classe por uma que consulte o banco - `AuthService` e os endpoints nao
mudam. Os endpoints de negocio ainda nao exigem token; para exigir, adicione
`dependencies=[Depends(get_current_subject)]` ao router em `api/v1/__init__.py`.

## Observabilidade

Tres sinais, identicos em local e no cluster:

- **Metricas** em `/metrics`, com a rota *parametrizada* como label
  (`/orders/{order_id}`, nunca `/orders/abc-123`) - o caminho concreto criaria
  uma serie temporal por id e derrubaria o Prometheus.
- **Logs** em JSON estruturado via `structlog`. Cada requisicao carrega um
  `request_id` (header `X-Request-ID`, gerado se ausente) que aparece em todas
  as linhas daquela requisicao e vira label no Loki.
- **Health**: `/health/live` (o processo esta vivo) e `/health/ready` (as
  dependencias respondem). Liveness nao consulta o banco de proposito: se
  consultasse, uma oscilacao do Postgres faria o Kubernetes reiniciar pods
  saudaveis.

## Testes

| Suite                | O que cobre                                        | Precisa de banco |
| -------------------- | -------------------------------------------------- | ---------------- |
| `tests/unit/`        | invariantes dos modelos, regras dos services, HTTP  | nao              |
| `tests/integration/` | mapeamento ORM, transacoes, concorrencia, API real  | sim              |

Os testes de service usam `tests/fakes/unit_of_work.py` - implementacoes em
memoria das mesmas portas. Nao sao mocks que devolvem o que o teste espera:
sao repositorios de verdade, so que sem I/O. Se a regra estiver errada, o teste
falha.

## Deploy

A aplicacao e implantada pelo chart em `infra/helm/order-management`, com um
arquivo de valores por ambiente sobreposto ao padrao:

```bash
helm upgrade --install order-management infra/helm/order-management \
  --values infra/helm/order-management/values.yaml \
  --values infra/helm/order-management/values-staging.yaml \
  --set image.tag=<sha-do-commit>
```

`image.tag` e obrigatorio - o chart falha sem ele. `latest` inviabiliza
rollback: nao ha como saber qual imagem estava rodando antes.

As migrations rodam como hook `pre-upgrade`: o schema fica pronto antes que
qualquer pod novo receba trafego, e o release nao avanca se o job falhar.

O pipeline hoje constroi as imagens mas nao as publica nem implanta. O
`helm upgrade` e executado manualmente; no ambiente local, `make minikube-up`
faz o ciclo completo (cluster, Postgres, imagens e release).
