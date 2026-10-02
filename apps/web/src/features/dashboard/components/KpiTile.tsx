import type { ReactNode } from 'react'

import { Sparkline } from '@/shared/charts/Sparkline'
import { IconTrendUp } from '@/shared/ui/icons'

export interface Delta {
  /** Variacao percentual contra o periodo anterior. */
  percent: number
  label: string
}

export type KpiHue = 'blue' | 'pink' | 'orange' | 'teal' | 'violet'

interface KpiTileProps {
  icon: ReactNode
  label: string
  value: ReactNode
  hint?: string
  delta?: Delta | undefined
  trend?: number[] | undefined
  /** Cor do icone. Decorativa: o rotulo e que identifica o indicador. */
  hue?: KpiHue
  tone?: 'neutral' | 'warn' | 'critical'
}

export function KpiTile({
  icon,
  label,
  value,
  hint,
  delta,
  trend,
  hue = 'blue',
  tone = 'neutral',
}: KpiTileProps) {
  // Aqui subir e sempre bom (pedidos, faturamento). Num indicador de devolucao
  // ou ruptura a direcao teria de ser informada pelo chamador.
  const direcao = delta === undefined ? null : delta.percent >= 0 ? 'up' : 'down'

  return (
    <article className="kpi" data-hue={hue} data-tone={tone === 'neutral' ? undefined : tone}>
      <div className="kpi__head">
        <span className="kpi__icon" aria-hidden="true">
          {icon}
        </span>
        <p className="kpi__label">{label}</p>
      </div>

      <div className="kpi__body">
        <p className="kpi__value">{value}</p>
        {delta ? (
          <p className="kpi__delta" data-direction={direcao}>
            <span className="kpi__delta-value">
              <IconTrendUp size={13} />
              {delta.percent >= 0 ? '+' : ''}
              {delta.percent}%
            </span>
            <span className="kpi__delta-label">{delta.label}</span>
          </p>
        ) : null}
      </div>

      {delta ? null : <p className="kpi__hint">{hint ?? ' '}</p>}

      {trend ? <Sparkline values={trend} /> : null}
    </article>
  )
}
