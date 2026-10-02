/**
 * Serie temporal de uma unica medida.
 *
 * Uma serie so, entao nao ha legenda: o titulo do cartao ja diz o que esta
 * plotado. O eixo Y e o tooltip carregam os valores que nao sao rotulados
 * diretamente.
 */

import {
  useEffect,
  useId,
  useRef,
  useState,
  type PointerEvent as ReactPointerEvent,
} from 'react'

import { caminhoSuave } from '@/shared/charts/curve'
import { useI18n } from '@/shared/i18n/useI18n'

export interface TrendPoint {
  date: string
  value: number
}

interface TrendChartProps {
  points: TrendPoint[]
  /** Como escrever o valor no tooltip e no eixo. */
  format: (value: number) => string
  /** Nome da serie no tooltip (ex.: "pedidos"). */
  label: string
  /** Descricao do grafico inteiro para tecnologia assistiva. */
  description: string
}

// Tamanho usado antes da primeira medicao (e em ambiente sem layout, como
// nos testes): proporcao de um cartao largo.
const TAMANHO_INICIAL = { width: 1200, height: 300 }
const PADDING = { top: 18, right: 16, bottom: 34, left: 68 }

/** Arredonda o topo do eixo para um numero limpo (10, 50, 100, 500...). */
function niceCeiling(value: number): number {
  if (value <= 0) return 1
  const magnitude = 10 ** Math.floor(Math.log10(value))
  for (const step of [1, 2, 2.5, 5, 10]) {
    const candidate = step * magnitude
    if (candidate >= value) return candidate
  }
  return 10 * magnitude
}

/**
 * Mede a caixa do grafico. Desenhar no tamanho real, em vez de escalar um
 * viewBox fixo, mantem o texto dos eixos no corpo certo em qualquer largura e
 * deixa o grafico ocupar a altura que o cartao tiver.
 */
function useTamanho<T extends HTMLElement>() {
  const ref = useRef<T>(null)
  const [tamanho, setTamanho] = useState(TAMANHO_INICIAL)

  useEffect(() => {
    const elemento = ref.current
    if (!elemento || typeof ResizeObserver === 'undefined') return
    const observador = new ResizeObserver(([entrada]) => {
      if (!entrada) return
      const { width, height } = entrada.contentRect
      if (width > 0 && height > 0) setTamanho({ width: Math.round(width), height: Math.round(height) })
    })
    observador.observe(elemento)
    return () => observador.disconnect()
  }, [])

  return [ref, tamanho] as const
}

export function TrendChart({ points, format, label, description }: TrendChartProps) {
  const [caixaRef, { width: WIDTH, height: HEIGHT }] = useTamanho<HTMLDivElement>()
  const { format: formato } = useI18n()
  const PLOT_WIDTH = WIDTH - PADDING.left - PADDING.right
  const PLOT_HEIGHT = HEIGHT - PADDING.top - PADDING.bottom

  const [active, setActive] = useState<number | null>(null)
  // Id unico: dois graficos na mesma tela nao podem disputar o mesmo gradiente.
  const gradienteId = `trend-wash-${useId().replace(/:/g, '')}`

  const bruto = Math.max(...points.map((point) => point.value), 0)
  const serieInteira = points.every((point) => Number.isInteger(point.value))
  const maximo = serieInteira
    ? Math.max(2, Math.ceil(niceCeiling(bruto) / 2) * 2)
    : niceCeiling(bruto)
  const passo = points.length > 1 ? PLOT_WIDTH / (points.length - 1) : 0

  const x = (index: number) => PADDING.left + index * passo
  const y = (value: number) => PADDING.top + PLOT_HEIGHT - (value / maximo) * PLOT_HEIGHT

  const base = PADDING.top + PLOT_HEIGHT
  const linha = caminhoSuave(points.map((point, index) => [x(index), y(point.value)] as const))
  const area = `${linha} L ${x(points.length - 1)},${base} L ${PADDING.left},${base} Z`

  // Quatro faixas quando o topo divide inteiro; senao duas, para nunca
  // rotular meio pedido.
  const divisoes = serieInteira && maximo % 4 !== 0 ? 2 : 4
  const ticks = Array.from({ length: divisoes + 1 }, (_, indice) => (maximo / divisoes) * indice)
  const pontoAtivo = active === null ? null : points[active]
  const intervaloRotulo = Math.max(1, Math.ceil(72 / (passo || 1)))

  // O ponteiro mira em uma data, nunca em uma linha de 2px: a posicao vira
  // indice pela distancia horizontal.
  function handleMove(event: ReactPointerEvent<SVGSVGElement>) {
    const caixa = event.currentTarget.getBoundingClientRect()
    const relativo = ((event.clientX - caixa.left) / caixa.width) * WIDTH
    const indice = Math.round((relativo - PADDING.left) / (passo || 1))
    setActive(Math.min(Math.max(indice, 0), points.length - 1))
  }

  return (
    <div className="trend" ref={caixaRef}>
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        role="img"
        aria-label={description}
        onPointerMove={handleMove}
        onPointerLeave={() => setActive(null)}
      >
        <defs>
          {/* O preenchimento some em direcao a base: a area sugere volume sem
              competir com a linha, que e quem carrega o dado. */}
          <linearGradient id={gradienteId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--series)" stopOpacity="0.32" />
            <stop offset="100%" stopColor="var(--series)" stopOpacity="0" />
          </linearGradient>
        </defs>

        {ticks.map((tick) => (
          <g key={tick}>
            <line
              className="trend__grid"
              x1={PADDING.left}
              x2={WIDTH - PADDING.right}
              y1={y(tick)}
              y2={y(tick)}
            />
            <text className="trend__axis-label" x={PADDING.left - 10} y={y(tick) + 4} textAnchor="end">
              {format(tick)}
            </text>
          </g>
        ))}

        <path className="trend__area" d={area} fill={`url(#${gradienteId})`} />
        <path className="trend__line" d={linha} />

        {points.map((point, index) =>
          // Um rotulo a cada ~72px; o ultimo sempre aparece, e o vizinho
          // regular que ficaria colado nele cede o lugar.
          (index % intervaloRotulo === 0 && points.length - 1 - index >= intervaloRotulo / 2) ||
          index === points.length - 1 ? (
            <text
              key={point.date}
              className="trend__axis-label"
              x={x(index)}
              y={HEIGHT - 10}
              textAnchor="middle"
            >
              {formato.dayShort(point.date)}
            </text>
          ) : null,
        )}

        <circle
          className="trend__marker"
          cx={x(points.length - 1)}
          cy={y(points.at(-1)?.value ?? 0)}
          r="4.5"
        />

        {pontoAtivo && active !== null ? (
          <g>
            <line
              className="trend__crosshair"
              x1={x(active)}
              x2={x(active)}
              y1={PADDING.top}
              y2={PADDING.top + PLOT_HEIGHT}
            />
            <circle className="trend__marker" cx={x(active)} cy={y(pontoAtivo.value)} r="5" />
          </g>
        ) : null}
      </svg>

      {pontoAtivo && active !== null ? (
        <div
          className="trend__tooltip"
          style={{ left: `${(x(active) / WIDTH) * 100}%`, top: `${(y(pontoAtivo.value) / HEIGHT) * 100}%` }}
        >
          <p className="trend__tooltip-date">{formato.dayLong(pontoAtivo.date)}</p>
          <p className="trend__tooltip-row">
            <span className="trend__key" aria-hidden="true" />
            <span className="trend__tooltip-value">{format(pontoAtivo.value)}</span>
            <span className="trend__tooltip-label">{label}</span>
          </p>
        </div>
      ) : null}
    </div>
  )
}
