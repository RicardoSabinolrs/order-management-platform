import { beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * A flag precisa ser lida do ambiente, nao inferida do modo de execucao:
 * inferir de `import.meta.env.DEV` fazia o frontend ignorar a API real que
 * estava rodando ao lado durante o `make dev`.
 */
async function loadConfig(env: Record<string, string | undefined>) {
  vi.resetModules()
  vi.stubEnv('VITE_USE_MOCKS', env.VITE_USE_MOCKS ?? '')
  vi.stubEnv('VITE_API_BASE_URL', env.VITE_API_BASE_URL ?? '')
  const { config } = await import('@/shared/config/env')
  return config
}

beforeEach(() => {
  vi.unstubAllEnvs()
})

describe('config.useMocks', () => {
  it.each(['true', '1'])('liga quando VITE_USE_MOCKS=%s', async (value) => {
    expect((await loadConfig({ VITE_USE_MOCKS: value })).useMocks).toBe(true)
  })

  it.each(['false', '0', 'sim', ''])('desliga para %s', async (value) => {
    expect((await loadConfig({ VITE_USE_MOCKS: value })).useMocks).toBe(false)
  })

  it('desliga quando a variavel nao foi definida', async () => {
    expect((await loadConfig({})).useMocks).toBe(false)
  })
})

describe('config.apiBaseUrl', () => {
  it('e vazio por padrao, para usar o mesmo origin', async () => {
    expect((await loadConfig({})).apiBaseUrl).toBe('')
  })

  it('respeita a base configurada', async () => {
    const config = await loadConfig({ VITE_API_BASE_URL: 'https://api.exemplo.com' })
    expect(config.apiBaseUrl).toBe('https://api.exemplo.com')
  })
})
