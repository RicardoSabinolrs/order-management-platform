# Order Management Web

Painel de controle de pedidos e estoque. React 19 + TypeScript, Vite,
TanStack Query.

## Estrutura

```
src/
├── main.tsx            bootstrap (liga o MSW antes de renderizar)
├── app/                shell: providers, rotas, layout, estilos
├── features/           uma pasta por area de negocio
│   ├── auth/             login e sessao
│   ├── dashboard/        visao consolidada
│   ├── orders/           lista, detalhe e criacao de pedidos
│   ├── products/         CRUD do catalogo
│   ├── stock/            saldos, entradas e ajustes
│   └── health/           estado das dependencias da API
├── shared/             cliente HTTP, tipos da API, formatacao, UI comum
└── mocks/              handlers do MSW (dados de demonstracao)
```

Cada feature segue o mesmo desenho: `types.ts` (tipos da interface),
`api/` (chama a API e traduz os DTOs), `hooks/` (React Query),
`components/` e `pages/`.

## Configuracao

As variaveis vem do `.env` da **raiz do monorepo** (`envDir` no
`vite.config.ts`), nao de `apps/web/.env`. So as prefixadas com `VITE_` chegam
ao navegador.

| Variavel            | Padrao                  | Para que serve                                  |
| ------------------- | ----------------------- | ----------------------------------------------- |
| `VITE_USE_MOCKS`    | `false`                 | `true` sobe com dados de demonstracao (MSW)      |
| `VITE_API_BASE_URL` | vazio                   | Vazio = mesmo origin; o proxy encaminha a API    |
| `API_PROXY_TARGET`  | `http://localhost:8000` | Para onde o proxy do Vite encaminha em dev       |

Variavel de ambiente do shell tem precedencia sobre o `.env` - e o que permite
os alvos do `make` forcarem o modo.

## Rodando

```bash
pnpm dev                          # segue o VITE_USE_MOCKS do .env
VITE_USE_MOCKS=true  pnpm dev     # forca dados de demonstracao
VITE_USE_MOCKS=false pnpm dev     # forca a API real
pnpm test && pnpm lint && pnpm typecheck
```

Da raiz: `make dev-frontend` (mocado) ou `make frontend` (API real).

## Modo de demonstracao

Com `VITE_USE_MOCKS=true` a aplicacao sobe inteira sem backend, **desde a tela
de login**: o MSW e iniciado em `main.tsx` antes do primeiro render, senao a
primeira requisicao escaparia para a rede.

Os handlers em `src/mocks/handlers.ts` reproduzem o contrato real - incluindo
os erros em `problem+json` e as regras de estoque: pedir mais do que ha
disponivel devolve 409 tanto no mock quanto na API. Eles montam as rotas a
partir de `config.apiBaseUrl`, entao continuam casando mesmo se a base for
apontada para outro dominio.

As telas exibem um selo *dados de demonstracao* enquanto a flag esta ligada, o
formulario de login ja vem preenchido, e o servidor de dev anuncia o modo na
subida:

```
  ➜  modo:    dados de demonstracao (VITE_USE_MOCKS=true)
```

Com a flag desligada, o `import()` do MSW fica inalcancavel e o bundle do mock
(~267 kB) nao e sequer gerado no build.

### Nada escapa em silencio

Com os mocks ligados nao ha backend do outro lado, entao uma rota sem handler
nao pode simplesmente vazar para a rede - viraria `ECONNREFUSED`, um erro que
nao diz nada sobre a causa. Duas redes de seguranca evitam isso:

1. Um handler final em `handlers.ts` responde `501` a qualquer `/api/*` ou
   `/health/*` sem mock, dizendo qual rota falta.
2. Um middleware no `vite.config.ts` desliga o proxy nesse modo e responde com
   a mesma clareza, caso a requisicao chegue ao servidor de dev.

Os mesmos handlers rodam nos testes (`src/test/setup.ts`): a API se comporta de
um jeito so, definido em um lugar so.
