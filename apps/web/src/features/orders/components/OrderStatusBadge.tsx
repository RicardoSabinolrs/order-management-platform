import type { OrderStatus } from '@/features/orders/types'
import { useI18n } from '@/shared/i18n/useI18n'

export function OrderStatusBadge({ status }: { status: OrderStatus }) {
  const { t } = useI18n()
  return (
    <span className="badge" data-status={status}>
      {t.status[status]}
    </span>
  )
}
