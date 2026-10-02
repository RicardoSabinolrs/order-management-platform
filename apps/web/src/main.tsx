import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

import { App } from '@/app/App'
import { AppProviders } from '@/app/providers'
import '@/app/styles/index.css'
import { setMockTransport } from '@/mocks/mode'
import { config } from '@/shared/config/env'

/** Remove worker de mock deixado por uma sessao anterior. */
async function unregisterMockWorkers(): Promise<void> {
  if (!('serviceWorker' in navigator)) return

  const registros = await navigator.serviceWorker.getRegistrations()
  await Promise.all(
    registros
      .filter((registro) => registro.active?.scriptURL.includes('mockServiceWorker'))
      .map((registro) => registro.unregister()),
  )
}

/**
 * Prepara o modo de demonstracao.
 *
 * O caminho preferido e o service worker: a aplicacao faz `fetch` de verdade e
 * nao sabe que esta mocada. Mas ele nao esta disponivel em toda situacao -
 * contexto inseguro (abrir pelo IP da rede), janela privada de alguns
 * navegadores, politica de extensao - e pode demorar a assumir o controle da
 * aba. Quando nao da, os mesmos handlers respondem dentro da pagina, e o modo
 * de demonstracao funciona do mesmo jeito.
 */
async function prepareMocks(): Promise<void> {
  if (!config.useMocks) {
    // Trocar de modo com o worker antigo ainda registrado faria a API real
    // continuar sendo respondida por dados falsos.
    await unregisterMockWorkers()
    setMockTransport('off')
    return
  }

  if (!('serviceWorker' in navigator) || !window.isSecureContext) {
    setMockTransport('in-page')
    console.info(
      '%c[mocks] dados de demonstracao ativos (dentro da pagina)',
      'color:#9a6700;font-weight:600',
      '- sem service worker neste endereco; abra por localhost para usar a rede.',
    )
    return
  }

  try {
    const { worker } = await import('@/mocks/browser')
    const { keepMockWorkerAlive } = await import('@/mocks/keepalive')

    await worker.start({ onUnhandledFrame: 'bypass', quiet: true })

    if (navigator.serviceWorker.controller) {
      keepMockWorkerAlive()
      setMockTransport('worker')
      console.info(
        '%c[mocks] dados de demonstracao ativos',
        'color:#9a6700;font-weight:600',
        '- VITE_USE_MOCKS=false para falar com a API real.',
      )
      return
    }

    // Registrado, mas ainda sem controlar esta aba: so passaria a controlar no
    // proximo carregamento, e ate la tudo escaparia para a rede.
    setMockTransport('in-page')
    console.info(
      '%c[mocks] dados de demonstracao ativos (dentro da pagina)',
      'color:#9a6700;font-weight:600',
      '- o service worker ainda nao controla esta aba.',
    )
  } catch (error) {
    setMockTransport('in-page')
    console.warn('[mocks] service worker indisponivel, respondendo na pagina.', error)
  }
}

async function bootstrap(): Promise<void> {
  await prepareMocks()

  const container = document.getElementById('root')
  if (!container) {
    throw new Error('Elemento #root nao encontrado no index.html')
  }

  createRoot(container).render(
    <StrictMode>
      <BrowserRouter>
        <AppProviders>
          <App />
        </AppProviders>
      </BrowserRouter>
    </StrictMode>,
  )
}

void bootstrap()
