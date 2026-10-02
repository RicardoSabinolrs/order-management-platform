import { describe, expect, it } from 'vitest'

import { DEMO_CREDENTIALS } from '@/features/auth/demo'
import { resolveWithHandlers } from '@/mocks/transport'

/**
 * O transporte in-page e o plano B do modo de demonstracao: sem ele, um
 * navegador sem service worker (contexto inseguro, janela privada) manda toda
 * chamada para uma rede onde nao ha backend.
 */
describe('resolveWithHandlers', () => {
  it('responde o login com as credenciais de demonstracao', async () => {
    const response = await resolveWithHandlers(
      new Request(`${location.origin}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(DEMO_CREDENTIALS),
      }),
    )

    expect(response?.status).toBe(200)
    const body = (await response?.json()) as { access_token: string }
    expect(body.access_token).toBe('mock.access.token')
  })

  it('recusa credencial errada com 401', async () => {
    const response = await resolveWithHandlers(
      new Request(`${location.origin}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: DEMO_CREDENTIALS.email, password: 'errada' }),
      }),
    )

    expect(response?.status).toBe(401)
  })

  it('responde rotas autenticadas', async () => {
    const response = await resolveWithHandlers(
      new Request(`${location.origin}/api/v1/orders?page=1&page_size=10`, {
        headers: { Authorization: 'Bearer mock.access.token' },
      }),
    )

    expect(response?.status).toBe(200)
    const body = (await response?.json()) as { total: number }
    expect(body.total).toBeGreaterThan(0)
  })
})
