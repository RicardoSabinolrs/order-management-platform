import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderResult } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'

import { AuthProvider } from '@/features/auth/hooks/AuthProvider'
import type { Locale } from '@/shared/i18n/locale'
import { I18nProvider } from '@/shared/i18n/I18nProvider'
import { ThemeProvider } from '@/shared/theme/ThemeProvider'
import { ToastProvider } from '@/shared/toast/ToastProvider'

interface Options {
  route?: string
  /** Os testes leem os textos em portugues por padrao. */
  locale?: Locale
}

/** Monta um componente com os mesmos providers da aplicacao real. */
export function renderWithProviders(ui: ReactNode, { route = '/', locale = 'pt-BR' }: Options = {}): RenderResult {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })

  return render(
    <MemoryRouter initialEntries={[route]}>
      <I18nProvider initialLocale={locale}>
        <ThemeProvider>
          <QueryClientProvider client={queryClient}>
            <ToastProvider>
              <AuthProvider>{ui}</AuthProvider>
            </ToastProvider>
          </QueryClientProvider>
        </ThemeProvider>
      </I18nProvider>
    </MemoryRouter>,
  )
}
