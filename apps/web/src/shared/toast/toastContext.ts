import { createContext } from 'react'

export type ToastTone = 'success' | 'error' | 'info'

export interface Toast {
  id: number
  tone: ToastTone
  title: string
  detail?: string | undefined
}

export interface ToastContextValue {
  notify: (toast: Omit<Toast, 'id'>) => void
}

/**
 * Em arquivo separado do provider: um modulo que exporta componente e valor
 * nao-componente quebra o fast refresh do Vite.
 */
export const ToastContext = createContext<ToastContextValue | null>(null)
