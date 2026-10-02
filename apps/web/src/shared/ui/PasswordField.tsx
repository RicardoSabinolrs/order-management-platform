import { useId, useState, type InputHTMLAttributes } from 'react'

import { IconEye, IconEyeOff } from '@/shared/ui/icons'

interface PasswordFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string
  showLabel: string
  hideLabel: string
  error?: string | undefined
}

/**
 * Campo de senha com botao de revelar. Digitar senha longa sem ver e a causa
 * mais comum de "senha incorreta" que nao era.
 */
export function PasswordField({
  label,
  showLabel,
  hideLabel,
  error,
  className,
  ...inputProps
}: PasswordFieldProps) {
  const inputId = useId()
  const errorId = `${inputId}-error`
  const [visivel, setVisivel] = useState(false)

  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        {label}
      </label>
      <div className="input-group">
        <input
          id={inputId}
          type={visivel ? 'text' : 'password'}
          className={['input', error && 'input--invalid', className].filter(Boolean).join(' ')}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          {...inputProps}
        />
        <button
          type="button"
          className="input-group__action"
          aria-label={visivel ? hideLabel : showLabel}
          aria-pressed={visivel}
          aria-controls={inputId}
          onClick={() => setVisivel((atual) => !atual)}
        >
          {visivel ? <IconEyeOff size={17} /> : <IconEye size={17} />}
        </button>
      </div>
      {error ? (
        <p id={errorId} className="field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
