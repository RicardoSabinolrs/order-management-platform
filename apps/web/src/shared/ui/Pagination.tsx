import { useI18n } from '@/shared/i18n/useI18n'
import { Button } from '@/shared/ui/Button'
import { IconChevronLeft, IconChevronRight } from '@/shared/ui/icons'

interface PaginationProps {
  page: number
  pages: number
  total: number
  onChange: (page: number) => void
}

export function Pagination({ page, pages, total, onChange }: PaginationProps) {
  const { t } = useI18n()
  if (pages <= 1) return null

  return (
    <nav className="pagination" aria-label={t.common.paginationLabel}>
      <span className="pagination__status" aria-live="polite">
        {t.common.paginationStatus(page, pages, total)}
      </span>
      <div className="pagination__controls">
        <Button
          variant="secondary"
          size="sm"
          icon={<IconChevronLeft size={14} />}
          disabled={page <= 1}
          onClick={() => onChange(page - 1)}
        >
          {t.common.previous}
        </Button>
        <Button
          variant="secondary"
          size="sm"
          disabled={page >= pages}
          onClick={() => onChange(page + 1)}
        >
          {t.common.next}
          <IconChevronRight size={14} />
        </Button>
      </div>
    </nav>
  )
}
