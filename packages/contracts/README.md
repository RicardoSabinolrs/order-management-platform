# @oms/contracts

Reservado para os tipos TypeScript gerados a partir do OpenAPI da API.

Enquanto nao existe endpoint de negocio, o frontend declara seus tipos em
`apps/web/src/shared/api/`. Quando o primeiro contexto expuser rotas, a geracao
entra aqui e passa a ser a unica fonte de verdade - tipo escrito a mao dos dois
lados sai de sincronia sem ninguem perceber.
