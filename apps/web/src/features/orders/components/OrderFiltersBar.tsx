import { ORDER_STATUSES, type OrderStatus } from '@/features/orders/types'
import { useI18n } from '@/shared/i18n/useI18n'
import { IconSearch } from '@/shared/ui/icons'

interface OrderFiltersBarProps {
  status: OrderStatus | 'all'
  search: string
  onStatusChange: (status: OrderStatus | 'all') => void
  onSearchChange: (search: string) => void
}

export function OrderFiltersBar({
  status,
  search,
  onStatusChange,
  onSearchChange,
}: OrderFiltersBarProps) {
  const { t } = useI18n()

  return (
    <div className="toolbar">
      <label className="toolbar__search">
        <span className="visually-hidden">{t.orders.searchPlaceholder}</span>
        <IconSearch size={15} />
        <input
          type="search"
          className="input"
          placeholder={t.orders.searchPlaceholder}
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
        />
      </label>

      <div className="chips" role="group" aria-label={t.orders.filterByStatus}>
        <button
          type="button"
          className="chip"
          aria-pressed={status === 'all'}
          onClick={() => onStatusChange('all')}
        >
          {t.orders.all}
        </button>
        {ORDER_STATUSES.map((candidate) => (
          <button
            key={candidate}
            type="button"
            className="chip"
            aria-pressed={status === candidate}
            onClick={() => onStatusChange(candidate)}
          >
            {t.status[candidate]}
          </button>
        ))}
      </div>
    </div>
  )
}
