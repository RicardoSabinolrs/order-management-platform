import { type FormEvent, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'

import { LoginShowcase } from '@/features/auth/components/LoginShowcase'
import { DEMO_CREDENTIALS } from '@/features/auth/demo'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { ApiError } from '@/shared/api/problem'
import { config } from '@/shared/config/env'
import type { Dictionary } from '@/shared/i18n/locales/pt-BR'
import { useI18n } from '@/shared/i18n/useI18n'
import { Button } from '@/shared/ui/Button'
import { Field } from '@/shared/ui/Field'
import { IconAlert, IconChevronLeft, IconStock } from '@/shared/ui/icons'
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher'
import { PasswordField } from '@/shared/ui/PasswordField'
import { ThemeToggle } from '@/shared/ui/ThemeToggle'

interface FieldErrors {
  email?: string
  password?: string
}

function validate(email: string, password: string, t: Dictionary): FieldErrors {
  const errors: FieldErrors = {}
  if (!email.trim()) {
    errors.email = t.login.emailRequired
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    errors.email = t.common.invalidEmail
  }
  if (!password) {
    errors.password = t.login.passwordRequired
  } else if (password.length < 8) {
    errors.password = t.login.passwordMin
  }
  return errors
}

export function LoginPage() {
  const { signIn, isAuthenticated } = useAuth()
  const { t } = useI18n()
  const navigate = useNavigate()
  const location = useLocation()

  // No modo de demonstracao o formulario ja vem preenchido: nao ha razao para
  // fazer o usuario digitar uma credencial publica e fixa.
  const [email, setEmail] = useState(config.useMocks ? DEMO_CREDENTIALS.email : '')
  const [password, setPassword] = useState(config.useMocks ? DEMO_CREDENTIALS.password : '')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [formError, setFormError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  if (isAuthenticated) {
    return <Navigate to="/painel" replace />
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    const errors = validate(email, password, t)
    setFieldErrors(errors)
    if (Object.keys(errors).length > 0) return

    setSubmitting(true)
    try {
      await signIn({ email, password })
      // Volta para a tela que o usuario tentou abrir antes do login.
      const from = (location.state as { from?: string } | null)?.from ?? '/painel'
      void navigate(from, { replace: true })
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : t.login.genericError)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="login">
      <LoginShowcase />

      <div className="login__panel">
        <header className="login__toolbar">
          <Link className="login__back" to="/">
            <IconChevronLeft size={15} />
            {t.login.backToSite}
          </Link>
          <div className="login__prefs">
            <LanguageSwitcher compact />
            <ThemeToggle />
          </div>
        </header>

        <div className="login__card">
          <span className="login__card-mark" aria-hidden="true">
            <IconStock size={22} />
          </span>

          <div>
            <h1 className="login__title">{t.login.title}</h1>
            <p className="login__subtitle">{t.login.subtitle}</p>
          </div>

          <form className="login__form" onSubmit={(event) => void handleSubmit(event)} noValidate>
            {formError ? (
              <p className="alert alert--error" role="alert">
                <IconAlert size={15} />
                {formError}
              </p>
            ) : null}

            <Field
              label={t.common.email}
              type="email"
              name="email"
              autoComplete="username"
              placeholder={t.login.emailPlaceholder}
              value={email}
              error={fieldErrors.email}
              onChange={(event) => setEmail(event.target.value)}
            />

            <PasswordField
              label={t.common.password}
              showLabel={t.login.showPassword}
              hideLabel={t.login.hidePassword}
              name="password"
              autoComplete="current-password"
              placeholder="••••••••"
              value={password}
              error={fieldErrors.password}
              onChange={(event) => setPassword(event.target.value)}
            />

            <Button type="submit" className="login__submit" loading={submitting}>
              {submitting ? t.login.submitting : t.login.submit}
            </Button>
          </form>

          {config.useMocks ? (
            <p className="login__demo">
              <IconAlert size={15} />
              <span>
                {t.login.demoNotice} <code>{DEMO_CREDENTIALS.email}</code>
              </span>
            </p>
          ) : null}

          <p className="login__hint">{t.login.noAccount}</p>
        </div>
      </div>
    </div>
  )
}
