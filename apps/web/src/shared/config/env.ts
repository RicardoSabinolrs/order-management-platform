/**
 * Configuracao do frontend, resolvida uma vez no boot.
 *
 * As variaveis vem do `.env` da raiz do monorepo (ver `envDir` no
 * vite.config.ts). Somente as prefixadas com `VITE_` chegam ao navegador.
 */

interface AppConfig {
  /**
   * Base da API. Vazio significa mesmo origin: em desenvolvimento o proxy do
   * Vite encaminha `/api` e `/health` para o backend; em producao o nginx e o
   * ingress fazem o mesmo. E o padrao, e o que mantem o codigo sem URL
   * absoluta espalhada.
   */
  readonly apiBaseUrl: string

  /**
   * Liga o MSW: a aplicacao sobe inteira com dados de demonstracao, do login
   * em diante, sem backend no ar.
   */
  readonly useMocks: boolean
}

function readBoolean(value: string | undefined): boolean {
  return value === 'true' || value === '1'
}

export const config: AppConfig = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? '',
  // Sem fallback para `import.meta.env.DEV`: o modo precisa ser uma escolha
  // explicita. Ligar mock por ser desenvolvimento fazia o front ignorar a API
  // real que estava rodando ao lado.
  useMocks: readBoolean(import.meta.env.VITE_USE_MOCKS),
}
