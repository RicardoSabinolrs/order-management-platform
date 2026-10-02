import { describe, expect, it } from 'vitest'

import { server } from '@/mocks/server'

/**
 * A rede de seguranca existe para que nenhuma rota de API escape do MSW no
 * modo de demonstracao. Escapando, ela bateria no servidor de dev e voltaria
 * como erro de conexao - sem dizer o que faltou.
 */
describe('rede de seguranca dos mocks', () => {
  it('responde 501 para uma rota de API sem handler', async () => {
    const response = await fetch('/api/v1/rota-que-nao-existe', { method: 'POST' })

    expect(response.status).toBe(501)
    expect(response.headers.get('content-type')).toContain('application/problem+json')

    const problem = (await response.json()) as { code: string; detail: string }
    expect(problem.code).toBe('mock_nao_implementado')
    expect(problem.detail).toContain('/api/v1/rota-que-nao-existe')
  })

  it('nao engole as rotas que tem handler', async () => {
    const response = await fetch('/health/ready')

    expect(response.status).toBe(200)
    expect(await response.json()).toMatchObject({ status: 'ready' })
  })

  it('o MSW nunca deixa passar uma chamada de API para a rede', () => {
    // `onUnhandledFrame: 'error'` no setup dos testes ja garantiria isto, mas
    // o catch-all e o que sustenta a mesma promessa no navegador.
    expect(server.listHandlers().length).toBeGreaterThan(0)
  })
})
