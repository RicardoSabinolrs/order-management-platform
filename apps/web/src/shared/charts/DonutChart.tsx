/**
 * Rosca de participacao: quanto cada categoria pesa no todo.
 *
 * Aqui cada fatia precisa de cor propria - e o unico jeito de separar partes
 * de um mesmo anel. A cor nunca vem sozinha: a legenda ao lado repete rotulo,
 * contagem e percentual de cada fatia.
 */

export interface DonutDatum {
  key: string
  label: string
  value: number
  /** Cor da fatia, de preferencia um token (`var(--good)`). */
  color: string
}

interface DonutChartProps {
  data: DonutDatum[]
  /** Unidade lida no centro e por tecnologia assistiva (ex.: "pedidos"). */
  unit: string
  /** Descricao da rosca inteira, no idioma da tela. */
  ariaLabel: (total: number, unit: string) => string
}

const RAIO = 42
const CIRCUNFERENCIA = 2 * Math.PI * RAIO
// Folga entre fatias, em unidades do traco: separa as partes sem borda.
const FOLGA = 1.6

export function DonutChart({ data, unit, ariaLabel }: DonutChartProps) {
  const total = data.reduce((soma, entrada) => soma + entrada.value, 0)

  let acumulado = 0
  const fatias = data
    .filter((entrada) => entrada.value > 0)
    .map((entrada) => {
      const comprimento = (entrada.value / total) * CIRCUNFERENCIA
      const fatia = { ...entrada, comprimento, inicio: acumulado }
      acumulado += comprimento
      return fatia
    })
  const unica = fatias.length === 1

  return (
    <div className="donut">
      <div className="donut__figure">
        <svg viewBox="0 0 100 100" role="img" aria-label={ariaLabel(total, unit)}>
          <circle className="donut__track" cx="50" cy="50" r={RAIO} />
          {/* Gira o anel: a primeira fatia comeca no topo, como um relogio. */}
          <g transform="rotate(-90 50 50)">
            {fatias.map((fatia) => (
              <circle
                key={fatia.key}
                className="donut__slice"
                cx="50"
                cy="50"
                r={RAIO}
                stroke={fatia.color}
                strokeDasharray={`${Math.max(fatia.comprimento - (unica ? 0 : FOLGA), 0.01)} ${CIRCUNFERENCIA}`}
                strokeDashoffset={-fatia.inicio}
              />
            ))}
          </g>
        </svg>
        <div className="donut__center" aria-hidden="true">
          <span className="donut__total">{total}</span>
          <span className="donut__unit">{unit}</span>
        </div>
      </div>

      <ul className="donut__legend">
        {data.map((entrada) => (
          <li key={entrada.key} className="donut__item">
            <span className="donut__swatch" style={{ background: entrada.color }} aria-hidden="true" />
            <span className="donut__label">{entrada.label}</span>
            <span className="donut__value">{entrada.value}</span>
            <span className="donut__share">
              {total > 0 ? Math.round((entrada.value / total) * 100) : 0}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
