import { type FormEvent, useState } from 'react'

import { USER_ROLES, type UserDraft, type UserRole } from '@/features/users/types'
import { useI18n } from '@/shared/i18n/useI18n'
import { Button } from '@/shared/ui/Button'
import { Field } from '@/shared/ui/Field'

interface UserFormProps {
  submitting: boolean
  error?: string | undefined
  onSubmit: (draft: UserDraft) => void
  onCancel: () => void
}

interface Errors {
  name?: string
  email?: string
  password?: string
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
// Mesmo minimo do backend: validar aqui so poupa a ida ao servidor.
const PASSWORD_MIN = 8

export function UserForm({ submitting, error, onSubmit, onCancel }: UserFormProps) {
  const { t } = useI18n()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  // Operador por padrao: o perfil mais comum, e nao o mais poderoso.
  const [role, setRole] = useState<UserRole>('operator')
  const [errors, setErrors] = useState<Errors>({})

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const nextErrors: Errors = {}
    if (!name.trim()) nextErrors.name = t.users.nameRequired
    if (!EMAIL_PATTERN.test(email.trim())) nextErrors.email = t.common.invalidEmail
    if (password.length < PASSWORD_MIN) nextErrors.password = t.users.passwordMin

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    onSubmit({ name: name.trim(), email: email.trim().toLowerCase(), password, role })
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      {error ? (
        <p className="form__error" role="alert">
          {error}
        </p>
      ) : null}

      <Field
        label={t.common.name}
        value={name}
        error={errors.name}
        autoComplete="off"
        onChange={(event) => setName(event.target.value)}
      />
      <Field
        label={t.common.email}
        type="email"
        value={email}
        error={errors.email}
        autoComplete="off"
        onChange={(event) => setEmail(event.target.value)}
      />
      <Field
        label={t.common.password}
        type="password"
        value={password}
        error={errors.password}
        hint={t.users.passwordHint}
        autoComplete="new-password"
        onChange={(event) => setPassword(event.target.value)}
      />

      <fieldset className="fieldset">
        <legend className="field__label">{t.users.role}</legend>
        <div className="role-options">
          {USER_ROLES.map((candidate) => (
            <label key={candidate} className="role-option" data-checked={role === candidate}>
              <input
                type="radio"
                name="role"
                value={candidate}
                checked={role === candidate}
                onChange={() => setRole(candidate)}
              />
              <span className="role-option__title">{t.roles[candidate]}</span>
              <span className="role-option__hint">{t.users.roleHints[candidate]}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="form__actions">
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t.common.cancel}
        </Button>
        <Button type="submit" loading={submitting}>
          {t.users.register}
        </Button>
      </div>
    </form>
  )
}
