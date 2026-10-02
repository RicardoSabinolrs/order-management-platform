import { useI18n } from '@/shared/i18n/useI18n'

/** Tela de erro em componente proprio: a classe nao pode usar hooks. */
export function ErrorFallback({ error }: { error: Error }) {
  const { t } = useI18n()
  return (
    <div className="state state--error" role="alert">
      <p className="state__title">{t.common.somethingWrong}</p>
      <p className="state__description">{error.message}</p>
      <button className="btn btn--secondary" onClick={() => window.location.reload()}>
        {t.common.reload}
      </button>
    </div>
  )
}
