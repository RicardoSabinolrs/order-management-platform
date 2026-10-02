import { useCallback, useMemo, useRef, useState, type ReactNode } from 'react'

import { useI18n } from '@/shared/i18n/useI18n'
import { IconAlert, IconCheck, IconClose } from '@/shared/ui/icons'
import { ToastContext, type Toast, type ToastContextValue } from '@/shared/toast/toastContext'

const DISMISS_AFTER_MS = 5000

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const nextId = useRef(0)
  const { t } = useI18n()

  const dismiss = useCallback((id: number) => {
    setToasts((current) => current.filter((toast) => toast.id !== id))
  }, [])

  const notify = useCallback<ToastContextValue['notify']>(
    (toast) => {
      const id = nextId.current++
      setToasts((current) => [...current, { ...toast, id }])
      window.setTimeout(() => dismiss(id), DISMISS_AFTER_MS)
    },
    [dismiss],
  )

  const value = useMemo<ToastContextValue>(() => ({ notify }), [notify])

  return (
    <ToastContext.Provider value={value}>
      {children}
      {/* `aria-live` polido: o aviso e complementar, nunca a unica forma de
          saber o que aconteceu - a tela ja reflete a mudanca. */}
      <div className="toasts" role="status" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className="toast" data-tone={toast.tone}>
            <span className="toast__icon" data-tone={toast.tone}>
              {toast.tone === 'error' ? <IconAlert size={16} /> : <IconCheck size={16} />}
            </span>
            <div className="toast__body">
              <p className="toast__title">{toast.title}</p>
              {toast.detail ? <p className="toast__detail">{toast.detail}</p> : null}
            </div>
            <button
              type="button"
              className="modal__close"
              onClick={() => dismiss(toast.id)}
              aria-label={t.common.closeNotice}
            >
              <IconClose size={14} />
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}
