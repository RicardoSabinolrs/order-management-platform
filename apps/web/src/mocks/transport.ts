/**
 * Resolve uma requisicao direto pelos handlers, dentro da pagina.
 *
 * O caminho normal do modo de demonstracao e o service worker: a aplicacao faz
 * `fetch` de verdade e nao sabe que esta mocada. Mas service worker nao e
 * garantido - ele nao existe em contexto inseguro (abrir pelo IP da rede em
 * vez de localhost), e alguns navegadores o desabilitam em janela privada ou
 * por politica. Nesses casos toda chamada escaparia para a rede, onde nao ha
 * backend algum, e a aplicacao pareceria quebrada sem explicacao.
 *
 * Este transporte e o plano B: usa exatamente os mesmos handlers, entao a
 * resposta e identica - so nao passa pela camada de rede.
 */

import { handlers } from '@/mocks/handlers'

let contador = 0

/**
 * Identificador da requisicao para o handler.
 *
 * Nao usa `crypto.randomUUID()`: ele so existe em contexto seguro, que e
 * justamente o caso em que este transporte entra em acao. Chamar la quebraria
 * com TypeError, e o erro chegaria a tela como "nao foi possivel entrar".
 */
function proximoId(): string {
  contador += 1
  return `in-page-${contador}`
}

export async function resolveWithHandlers(request: Request): Promise<Response | null> {
  for (const handler of handlers) {
    // O handler consome o corpo: cada tentativa precisa do proprio clone.
    const result = await handler.run({
      request: request.clone(),
      requestId: proximoId(),
    })

    if (result?.response) return result.response
  }

  return null
}
