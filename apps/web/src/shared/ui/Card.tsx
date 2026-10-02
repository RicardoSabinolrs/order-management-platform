import type { ReactNode } from 'react'

interface CardProps {
  title?: string
  description?: string
  actions?: ReactNode
  /** `flush` remove o respiro interno: para tabelas que vao ate a borda. */
  padding?: 'normal' | 'flush'
  children: ReactNode
}

export function Card({ title, description, actions, padding = 'normal', children }: CardProps) {
  return (
    <section className="card">
      {title ?? actions ? (
        <header className="card__header">
          <div>
            {title ? <h2 className="card__title">{title}</h2> : null}
            {description ? <p className="card__description">{description}</p> : null}
          </div>
          {actions ? <div className="card__actions">{actions}</div> : null}
        </header>
      ) : null}
      <div className={padding === 'flush' ? 'card__body card__body--flush' : 'card__body'}>
        {children}
      </div>
    </section>
  )
}
