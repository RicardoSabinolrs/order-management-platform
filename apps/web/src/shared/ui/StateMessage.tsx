import type { ReactNode } from 'react'

import { IconAlert, IconInbox } from '@/shared/ui/icons'

interface StateMessageProps {
  kind: 'empty' | 'error'
  title: string
  description?: string
  action?: ReactNode
}

/** Vazio e erro com a mesma anatomia em toda a aplicacao. */
export function StateMessage({ kind, title, description, action }: StateMessageProps) {
  return (
    <div className={`state state--${kind}`} role={kind === 'error' ? 'alert' : 'status'}>
      <span className="state__icon">
        {kind === 'error' ? <IconAlert size={20} /> : <IconInbox size={20} />}
      </span>
      <p className="state__title">{title}</p>
      {description ? <p className="state__description">{description}</p> : null}
      {action}
    </div>
  )
}
