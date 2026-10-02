/**
 * Cliente HTTP da aplicacao.
 *
 * Centraliza base URL, token, serializacao e traducao de erro. Nenhuma tela
 * chama `fetch` diretamente.
 */

import { getMockTransport } from '@/mocks/mode'
import { ApiError, isProblem, type Problem } from '@/shared/api/problem'
import { config } from '@/shared/config/env'

const TOKEN_STORAGE_KEY = 'oms.access_token'

/**
 * Codigo devolvido pelo guard do servidor de dev quando uma chamada de API
 * escapa do MSW - ver `mockModeGuard` no vite.config.ts.
 */
const MOCK_ESCAPE_CODE = 'mock_nao_interceptado'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY)
}

export function storeToken(token: string): void {
  localStorage.setItem(TOKEN_STORAGE_KEY, token)
}

export function clearStoredToken(): void {
  localStorage.removeItem(TOKEN_STORAGE_KEY)
}

interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown
  /** Rotas publicas (login) nao devem mandar Authorization. */
  anonymous?: boolean
}

/**
 * Reinscreve a aba no worker de mock e aguarda a mensagem ser processada.
 *
 * O worker pode ter sido encerrado por ociosidade entre o carregamento da
 * pagina e esta chamada; sem isto a proxima tentativa escaparia de novo.
 */
async function recoverMockTransport(): Promise<void> {
  const { activateMockWorker } = await import('@/mocks/keepalive')
  const { setMockTransport } = await import('@/mocks/mode')

  // Reinscreve a aba no worker; se ele nao voltar a controlar, a proxima
  // tentativa ja sai pelo transporte in-page.
  activateMockWorker()
  await new Promise((resolve) => setTimeout(resolve, 60))

  if (!navigator.serviceWorker?.controller) {
    setMockTransport('in-page')
  }
}

async function send(path: string, options: RequestOptions): Promise<Response> {
  const { body, anonymous = false, headers, ...init } = options
  const token = anonymous ? null : getStoredToken()

  const url = `${config.apiBaseUrl}${path}`
  const requestInit: RequestInit = {
    ...init,
    headers: {
      Accept: 'application/json',
      ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  }

  // Sem service worker no ar, os handlers respondem aqui mesmo: a alternativa
  // seria vazar para uma rede onde nao ha backend nenhum.
  if (getMockTransport() === 'in-page') {
    const { resolveWithHandlers } = await import('@/mocks/transport')
    const mocked = await resolveWithHandlers(new Request(new URL(url, location.origin), requestInit))
    if (mocked) return mocked
  }

  return fetch(url, requestInit)
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response = await send(path, options)
  let payload: unknown = response.status === 204 ? null : await response.json().catch(() => null)

  // Escapou do mock por worker encerrado: reinscreve e tenta uma vez. Sem
  // isto, ficar parado na tela por meio minuto quebraria a proxima acao.
  if (
    config.useMocks &&
    !response.ok &&
    isProblem(payload) &&
    payload.code === MOCK_ESCAPE_CODE
  ) {
    await recoverMockTransport()
    response = await send(path, options)
    payload = response.status === 204 ? null : await response.json().catch(() => null)
  }

  if (response.status === 204) {
    return undefined as T
  }

  if (!response.ok) {
    throw new ApiError(
      isProblem(payload)
        ? payload
        : ({
            type: 'about:blank',
            title: 'Falha na requisicao',
            status: response.status,
            detail: response.statusText || 'Nao foi possivel completar a requisicao.',
            code: 'http_error',
            instance: path,
          } satisfies Problem),
    )
  }

  return payload as T
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'GET' }),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'POST', body }),
  patch: <T>(path: string, body?: unknown, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'PATCH', body }),
  delete: <T>(path: string, options?: RequestOptions) =>
    request<T>(path, { ...options, method: 'DELETE' }),
}
