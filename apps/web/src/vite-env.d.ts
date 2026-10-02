/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Vazio = mesmo origin (o proxy do Vite encaminha para o backend). */
  readonly VITE_API_BASE_URL?: string
  /** "true" sobe a aplicacao com dados de demonstracao (MSW). */
  readonly VITE_USE_MOCKS?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
