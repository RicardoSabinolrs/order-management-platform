/**
 * Mantem esta aba inscrita no service worker do MSW.
 *
 * O worker guarda os clientes ativos em memoria (`activeClientIds`) e o
 * navegador encerra service workers ociosos - no Chrome, por volta de 30
 * segundos sem eventos. Ao ser revivido por uma requisicao, ele volta com o
 * conjunto vazio e cai no `if (activeClientIds.size === 0) return`, deixando a
 * chamada passar direto para a rede.
 *
 * O efeito e traicoeiro: o mock funciona no instante em que a pagina carrega e
 * "some" quando o usuario demora para clicar. Reenviar `MOCK_ACTIVATE` em
 * intervalo menor que o tempo de ocioso mantem o worker vivo e reinscreve a
 * aba caso ele tenha morrido.
 */

const PING_INTERVAL_MS = 15_000

export function activateMockWorker(): void {
  navigator.serviceWorker?.controller?.postMessage('MOCK_ACTIVATE')
}

export function keepMockWorkerAlive(): void {
  if (!('serviceWorker' in navigator)) return

  activateMockWorker()
  window.setInterval(activateMockWorker, PING_INTERVAL_MS)

  // Em aba oculta o navegador estrangula os timers, entao o worker pode morrer
  // mesmo com o intervalo acima. Reinscreve ao voltar o foco.
  document.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') activateMockWorker()
  })

  navigator.serviceWorker.addEventListener('controllerchange', activateMockWorker)
}
