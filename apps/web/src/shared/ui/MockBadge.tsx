import { config } from '@/shared/config/env'
import { useI18n } from '@/shared/i18n/useI18n'

/**
 * Marca visivel de que a tela esta com dados de demonstracao.
 *
 * Sem ela, uma sessao mocada e indistinguivel de uma real - e alguem acaba
 * reportando como bug um numero que nunca saiu do banco.
 */
export function MockBadge() {
  const { t } = useI18n()
  if (!config.useMocks) return null

  return (
    <span className="mock-badge" title="VITE_USE_MOCKS=true">
      {t.common.demoBadge}
    </span>
  )
}
