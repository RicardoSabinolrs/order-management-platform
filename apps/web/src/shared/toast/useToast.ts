import { useContext } from 'react'

import { ToastContext, type ToastContextValue } from '@/shared/toast/toastContext'

export function useToast(): ToastContextValue {
  const context = useContext(ToastContext)
  if (context === null) {
    throw new Error('useToast precisa estar dentro de <ToastProvider>.')
  }
  return context
}
