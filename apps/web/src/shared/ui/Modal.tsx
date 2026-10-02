import { useEffect, useRef, type ReactNode } from 'react'

import { useI18n } from '@/shared/i18n/useI18n'
import { IconClose } from '@/shared/ui/icons'

interface ModalProps {
  title: string
  open: boolean
  onClose: () => void
  children: ReactNode
}

/**
 * Dialogo sobre o `<dialog>` nativo: foco preso, Esc fecha e leitores de tela
 * anunciam - sem biblioteca e sem reimplementar acessibilidade.
 */
export function Modal({ title, open, onClose, children }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const { t } = useI18n()

  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return

    if (open && !dialog.open) dialog.showModal()
    if (!open && dialog.open) dialog.close()
  }, [open])

  return (
    <dialog ref={dialogRef} className="modal" onClose={onClose} onCancel={onClose}>
      <header className="modal__header">
        <h2 className="modal__title">{title}</h2>
        <button type="button" className="modal__close" onClick={onClose} aria-label={t.common.close}>
          <IconClose size={16} />
        </button>
      </header>
      <div className="modal__body">{children}</div>
    </dialog>
  )
}
