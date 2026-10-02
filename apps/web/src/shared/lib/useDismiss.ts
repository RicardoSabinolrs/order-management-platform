import { useEffect, type RefObject } from 'react'

/**
 * Fecha um menu flutuante com clique fora ou Esc - o comportamento que todo
 * usuario espera de um dropdown e que o navegador nao da de graca.
 */
export function useDismiss(
  ref: RefObject<HTMLElement | null>,
  open: boolean,
  onDismiss: () => void,
): void {
  useEffect(() => {
    if (!open) return

    function onPointer(event: PointerEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) onDismiss()
    }
    function onKey(event: KeyboardEvent) {
      if (event.key === 'Escape') onDismiss()
    }

    document.addEventListener('pointerdown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('pointerdown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [ref, open, onDismiss])
}
