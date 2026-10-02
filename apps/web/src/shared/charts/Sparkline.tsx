import { caminhoSuave } from '@/shared/charts/curve'

/**
 * Mini serie dentro de um indicador.
 *
 * Sem eixo, sem rotulo e sem tooltip: a sparkline mostra a forma do periodo,
 * nao valores. O numero exato esta no proprio indicador, logo acima.
 */
export function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2) return null

  const largura = 120
  const altura = 28
  const respiro = 3
  const passo = largura / (values.length - 1)

  const minimo = Math.min(...values)
  const maximo = Math.max(...values)
  const amplitude = maximo - minimo || 1

  const pontos = values.map(
    (valor, indice) =>
      [indice * passo, altura - respiro - ((valor - minimo) / amplitude) * (altura - respiro * 2)] as const,
  )

  const linha = caminhoSuave(pontos)
  const ultimo = pontos.at(-1) ?? [0, 0]

  return (
    <svg
      className="spark"
      viewBox={`0 0 ${largura} ${altura}`}
      // Estica na largura do cartao: com a razao preservada a serie ficaria
      // encolhida no meio do espaco disponivel.
      preserveAspectRatio="none"
      aria-hidden="true"
    >
      <path className="spark__area" d={`${linha} L ${largura},${altura} L 0,${altura} Z`} />
      <path className="spark__line" d={linha} />
      {/* Anel na cor da superficie: o ponto final continua legivel sobre a linha. */}
      <circle className="spark__end" cx={ultimo[0]} cy={ultimo[1]} r="2.5" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}
