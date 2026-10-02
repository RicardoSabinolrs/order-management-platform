import { caminhoSuave } from '@/shared/charts/curve'
import { useI18n } from '@/shared/i18n/useI18n'
import { IconStock, IconTrendUp } from '@/shared/ui/icons'

/**
 * Vitrine do produto ao lado do formulario.
 *
 * A previa e decorativa e estatica - marcada como `aria-hidden` para nao
 * poluir a leitura por tecnologia assistiva com numeros que nao sao dados.
 */

const SERIE = [14, 22, 18, 31, 27, 38, 34, 45, 41, 52]

function sparkline(): { linha: string; area: string } {
  const largura = 280
  const altura = 80
  const respiro = 8
  const passo = largura / (SERIE.length - 1)

  // Normaliza entre minimo e maximo: escalar a partir do zero deixaria a linha
  // achatada no topo da caixa, sem leitura de variacao.
  const minimo = Math.min(...SERIE)
  const maximo = Math.max(...SERIE)
  const amplitude = maximo - minimo || 1

  const pontos = SERIE.map(
    (valor, indice) =>
      [indice * passo, altura - respiro - ((valor - minimo) / amplitude) * (altura - respiro * 2)] as const,
  )
  const linha = caminhoSuave(pontos)
  return { linha, area: `${linha} L ${largura},${altura} L 0,${altura} Z` }
}

export function LoginShowcase() {
  const { t } = useI18n()
  const { linha, area } = sparkline()

  const pedidos = [
    { ref: 'PED-000142', status: 'delivered' },
    { ref: 'PED-000141', status: 'shipped' },
    { ref: 'PED-000140', status: 'pending' },
  ] as const

  return (
    <aside className="showcase">
      <div className="showcase__glow" aria-hidden="true" />

      <p className="showcase__brand">
        <span className="showcase__mark" aria-hidden="true">
          <IconStock size={19} />
        </span>
        Order Management
      </p>

      <div className="showcase__body">
        <span className="showcase__eyebrow">{t.login.showcaseEyebrow}</span>
        <h2 className="showcase__headline">{t.login.showcaseHeadline}</h2>
        <p className="showcase__lede">{t.login.showcaseLede}</p>

        <div className="preview" aria-hidden="true">
          <div className="preview__card preview__card--chart">
            <div className="preview__chart-head">
              <span className="preview__label">{t.login.showcaseRevenue}</span>
              <span className="preview__trend">
                <IconTrendUp size={13} />
                +18%
              </span>
            </div>
            <p className="preview__value">R$ 48,2k</p>
            <svg viewBox="0 0 280 80" preserveAspectRatio="none">
              <defs>
                <linearGradient id="showcase-wash" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#fff" stopOpacity="0.45" />
                  <stop offset="100%" stopColor="#fff" stopOpacity="0" />
                </linearGradient>
              </defs>
              <path d={area} fill="url(#showcase-wash)" />
              <path className="preview__line" d={linha} />
            </svg>
          </div>

          <div className="preview__row">
            <div className="preview__card">
              <p className="preview__label">{t.login.showcaseOpen}</p>
              <p className="preview__value">18</p>
            </div>
            <div className="preview__card">
              <p className="preview__label">{t.login.showcaseReserved}</p>
              <p className="preview__value">64</p>
            </div>
          </div>

          <div className="preview__card preview__orders">
            {pedidos.map((pedido) => (
              <div key={pedido.ref} className="preview__order">
                <span className="preview__ref">{pedido.ref}</span>
                <span className="preview__pill" data-status={pedido.status}>
                  {t.status[pedido.status]}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <p className="showcase__legal">{t.login.legal}</p>
    </aside>
  )
}
