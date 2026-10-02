import type { ButtonHTMLAttributes, ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md'
  loading?: boolean
  icon?: ReactNode
  children: ReactNode
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  disabled,
  children,
  className,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={['btn', `btn--${variant}`, size === 'sm' && 'btn--sm', className]
        .filter(Boolean)
        .join(' ')}
      disabled={disabled ?? loading}
      // Leitores de tela precisam saber que a acao esta em curso.
      aria-busy={loading}
      {...rest}
    >
      {loading ? <span className="spinner" aria-hidden="true" /> : icon}
      {children}
    </button>
  )
}
