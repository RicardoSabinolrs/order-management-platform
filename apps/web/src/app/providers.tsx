import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'

import { AuthProvider } from '@/features/auth/hooks/AuthProvider'
import { I18nProvider } from '@/shared/i18n/I18nProvider'
import { ThemeProvider } from '@/shared/theme/ThemeProvider'
import { ApiError } from '@/shared/api/problem'
import { ToastProvider } from '@/shared/toast/ToastProvider'
import { ErrorBoundary } from '@/shared/ui/ErrorBoundary'

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 30_000,
        refetchOnWindowFocus: false,
        retry: (failureCount, error) => {
          // 4xx nao melhora com nova tentativa: so atrasa a mensagem de erro.
          if (error instanceof ApiError && error.status < 500) return false
          return failureCount < 2
        },
      },
      mutations: { retry: false },
    },
  })
}

export function AppProviders({ children }: { children: ReactNode }) {
  // Dentro de estado: no StrictMode o componente monta duas vezes, e criar o
  // client no corpo descartaria o cache a cada render.
  const [queryClient] = useState(createQueryClient)

  return (
    // Idioma e tema por fora de tudo: ate a tela de erro precisa deles.
    <I18nProvider>
      <ThemeProvider>
        <ErrorBoundary>
          <QueryClientProvider client={queryClient}>
            <ToastProvider>
              <AuthProvider>{children}</AuthProvider>
            </ToastProvider>
          </QueryClientProvider>
        </ErrorBoundary>
      </ThemeProvider>
    </I18nProvider>
  )
}
