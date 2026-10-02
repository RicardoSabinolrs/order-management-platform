/**
 * Como as chamadas de API sao respondidas no modo de demonstracao.
 *
 * `worker`    o service worker intercepta na rede (caminho preferido: a
 *             aplicacao faz `fetch` normalmente).
 * `in-page`   os handlers respondem dentro da pagina, sem rede.
 * `off`       modo de demonstracao desligado; fala com a API real.
 */
export type MockTransport = 'worker' | 'in-page' | 'off'

let transport: MockTransport = 'off'

export function setMockTransport(next: MockTransport): void {
  transport = next
}

export function getMockTransport(): MockTransport {
  return transport
}
