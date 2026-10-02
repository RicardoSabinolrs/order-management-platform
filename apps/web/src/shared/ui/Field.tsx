import type { InputHTMLAttributes } from 'react'
import { useId } from 'react'

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string | undefined
  hint?: string | undefined
}

export function Field({ label, error, hint, className, ...inputProps }: FieldProps) {
  const inputId = useId()
  const errorId = `${inputId}-error`
  const hintId = `${inputId}-hint`

  const describedBy = [error ? errorId : null, hint ? hintId : null].filter(Boolean).join(' ')

  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        {label}
      </label>
      <input
        id={inputId}
        className={['input', error && 'input--invalid', className].filter(Boolean).join(' ')}
        aria-invalid={error ? true : undefined}
        // Liga erro e dica ao campo para tecnologia assistiva.
        aria-describedby={describedBy || undefined}
        {...inputProps}
      />
      {hint && !error ? (
        <p id={hintId} className="field__hint">
          {hint}
        </p>
      ) : null}
      {error ? (
        <p id={errorId} className="field__error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}
