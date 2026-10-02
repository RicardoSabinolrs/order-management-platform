# Registro de decisoes

Decisoes que moldaram o desenho atual, com o motivo. Serve para que uma escolha
deliberada nao seja desfeita por engano mais tarde.

## Organizacao por camada tecnica, nao por bounded context

**Decisao.** O backend e dividido em `api/`, `domain/{model,schema,repository,service}`,
`infra/` e `security/`.

**Por que.** E a convencao mais comum em FastAPI e facilita achar as coisas
enquanto o dominio e pequeno.

**Custo aceito.** Quando o dominio crescer, `model/` e `service/` vao acumular
assuntos que nao se falam. O sinal para reavaliar e quando duas areas de
negocio comecarem a mudar por motivos independentes.

## Estoque separado do produto

**Decisao.** `Product` e `StockItem` sao agregados distintos, ligados pelo
mesmo id.

**Por que.** Ajuste de preco e baixa de estoque tem frequencias e donos
diferentes. Juntos, disputariam a mesma linha e o mesmo lock.

## Reserva em vez de baixa imediata

**Decisao.** Criar um pedido reserva; enviar baixa.

**Por que.** Entre criar e enviar, a mercadoria ainda esta no deposito mas nao
pode ser vendida de novo. Sem a distincao, ou o estoque mente (baixa antes do
envio) ou vende duas vezes (baixa so no envio).

## `SELECT ... FOR UPDATE` na reserva

**Decisao.** `StockRepository.get_for_update` trava a linha.

**Por que.** Reservar e ler-decidir-escrever. Lock otimista resolveria com
retry, mas em um caminho de alta contencao (produto popular) o retry vira
tempestade. O lock pessimista e mais simples e o escopo e uma linha.

## Preco copiado para o item do pedido

**Decisao.** `OrderItem` guarda SKU, descricao e preco; nao referencia o
produto para exibicao.

**Por que.** O pedido e um registro do que foi combinado. Mudar a tabela de
precos nao pode reescrever o historico.

## Erros de dominio traduzidos em um unico lugar

**Decisao.** Services levantam `ApplicationError`; `api/errors.py` mapeia para
HTTP.

**Por que.** O dominio nao deve conhecer HTTP - ele tambem sera chamado por
consumers de fila e por scripts. E o mapeamento em um lugar so evita que a
mesma falha vire 400 em uma rota e 409 em outra.

## Corpo de erro no formato RFC 9457

**Decisao.** `application/problem+json`, com `code` na linguagem do negocio e
campos extras acionaveis.

**Por que.** O cliente precisa de mais do que "409". `insufficient_stock` com
`requested` e `available` permite a interface dizer exatamente o que fazer.

## Dinheiro em centavos

**Decisao.** `Money` guarda inteiros.

**Por que.** Ponto flutuante binario nao representa `0.10` exatamente. Um
centavo por transacao vira divergencia contabil no fechamento.

## Liveness nao consulta o banco

**Decisao.** `/health/live` responde sem tocar em dependencia alguma.

**Por que.** Liveness que depende do banco faz o Kubernetes reiniciar pods
saudaveis quando o Postgres oscila - piorando exatamente o momento em que se
precisa de estabilidade. Quem tira o pod do balanceador e o readiness.

## Migrations como hook `pre-upgrade` do Helm

**Decisao.** O job roda antes de os Deployments serem atualizados.

**Por que.** O codigo novo so recebe trafego depois que o schema esta pronto.
Se a migration falhar, o release nao avanca.

## `image.tag` obrigatorio no chart

**Decisao.** O chart falha se a tag nao for informada.

**Por que.** `latest` torna o rollback imprevisivel: nao ha como saber qual
imagem estava rodando antes.

## MSW em vez de flag de mock no codigo

**Decisao.** Os mocks interceptam na camada de rede.

**Por que.** O codigo da aplicacao faz `fetch` de verdade e nao sabe que esta
mocado. Nao ha `if (useMocks)` espalhado, e os mesmos handlers servem aos
testes.
