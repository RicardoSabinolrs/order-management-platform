import { Component, type ErrorInfo, type ReactNode } from 'react'

import { ErrorFallback } from '@/shared/ui/ErrorFallback'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/**
 * Impede que um erro de render derrube a aplicacao inteira em tela branca.
 * Precisa ser classe: nao existe equivalente em hooks.
 */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    // Aqui entra o envio para o coletor de erros (Sentry, OTel) quando houver.
    console.error('Erro nao tratado na interface', error, info.componentStack)
  }

  override render(): ReactNode {
    if (this.state.error) {
      return <ErrorFallback error={this.state.error} />
    }
    return this.props.children
  }
}
