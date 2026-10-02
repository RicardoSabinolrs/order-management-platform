import { useQuery } from '@tanstack/react-query'

import { fetchReadiness } from '@/features/health/api/health'
import { useI18n } from '@/shared/i18n/useI18n'
import { Card } from '@/shared/ui/Card'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

export function HealthPage() {
  const { t } = useI18n()
  const { data, isPending, isError, error } = useQuery({
    queryKey: ['health', 'ready'],
    queryFn: fetchReadiness,
    refetchInterval: 15_000,
  })

  return (
    <Card
      title={t.health.title}
      description={t.health.description}
      padding="flush"
    >
      {isPending ? <SkeletonRows rows={2} /> : null}

      {isError ? (
        <StateMessage
          kind="error"
          title={t.health.loadError}
          description={error.message}
        />
      ) : null}

      {data ? (
        <div className="table-wrapper">
          <table className="table">
            <caption className="visually-hidden">{t.health.caption}</caption>
            <thead>
              <tr>
                <th scope="col">{t.health.colDependency}</th>
                <th scope="col">{t.health.colState}</th>
              </tr>
            </thead>
            <tbody>
              {data.dependencies.map((dependency) => (
                <tr key={dependency.name}>
                  <td className="table__primary">{dependency.name}</td>
                  <td>
                    <span
                      className="badge"
                      data-status={dependency.healthy ? 'delivered' : 'cancelled'}
                    >
                      {dependency.healthy ? t.health.up : t.health.down}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </Card>
  )
}
