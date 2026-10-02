/**
 * Medidor de um percentual, em arco segmentado.
 *
 * Mostra uma proporcao so, contra o teto de 100%. O numero exato fica no
 * centro: o arco da a leitura de relance, o texto da o valor.
 */

interface GaugeProps {
  /** De 0 a 100. */
  percent: number
  label: string
}

const SEGMENTOS = 36
// Arco de 240 graus, aberto embaixo, comecando a 150 graus (sentido horario).
const INICIO = 150
const ABERTURA = 240

const R_INTERNO = 36
const R_EXTERNO = 47

function ponto(raio: number, graus: number): [number, number] {
  const radianos = (graus * Math.PI) / 180
  return [50 + raio * Math.cos(radianos), 50 + raio * Math.sin(radianos)]
}

export function Gauge({ percent, label }: GaugeProps) {
  const limitado = Math.min(Math.max(percent, 0), 100)
  const acesos = Math.round((limitado / 100) * SEGMENTOS)

  return (
    <div className="gauge">
      <svg viewBox="0 0 100 86" role="img" aria-label={`${label}: ${Math.round(limitado)}%`}>
        {Array.from({ length: SEGMENTOS }, (_, indice) => {
          const angulo = INICIO + (indice / (SEGMENTOS - 1)) * ABERTURA
          const [x1, y1] = ponto(R_INTERNO, angulo)
          const [x2, y2] = ponto(R_EXTERNO, angulo)
          return (
            <line
              key={indice}
              className="gauge__tick"
              data-on={indice < acesos}
              x1={x1}
              y1={y1}
              x2={x2}
              y2={y2}
            />
          )
        })}
      </svg>
      <div className="gauge__center" aria-hidden="true">
        <span className="gauge__value">{Math.round(limitado)}%</span>
        <span className="gauge__label">{label}</span>
      </div>
    </div>
  )
}
