import { caminhoSuave } from '@/shared/charts/curve'
import { useI18n } from '@/shared/i18n/useI18n'
import { IconDashboard, IconOrders, IconProducts, IconStock, IconUsers } from '@/shared/ui/icons'

/**
 * Miniatura do painel para o hero do site.
 *
 * Desenhada em HTML e SVG, nao como print: acompanha tema e idioma, e nunca
 * fica desatualizada em relacao a interface real. Os numeros sao ilustrativos
 * e a figura inteira e decorativa para tecnologia assistiva.
 */

const SERIE_A = [18, 26, 22, 34, 30, 42, 38, 52, 47, 58, 54, 66]
const SERIE_B = [10, 14, 18, 16, 24, 20, 28, 26, 34, 30, 38, 36]

function caminho(serie: number[], largura: number, altura: number): string {
  const maximo = Math.max(...SERIE_A)
  const passo = largura / (serie.length - 1)
  return caminhoSuave(serie.map((valor, i) => [i * passo, altura - (valor / maximo) * (altura - 8)] as const))
}

export function ProductPreview() {
  const { t } = useI18n()
  const largura = 420
  const altura = 130
  const linhaA = caminho(SERIE_A, largura, altura)
  const linhaB = caminho(SERIE_B, largura, altura)

  const kpis = [
    { label: t.dashboard.openOrders, value: '128', hue: 'blue', delta: '+12%' },
    { label: t.dashboard.revenue, value: 'R$ 48,2k', hue: 'pink', delta: '+18%' },
    { label: t.dashboard.averageTicket, value: 'R$ 376', hue: 'orange', delta: '+4%' },
  ] as const

  return (
    <figure className="product-preview" aria-label={t.landing.previewLabel}>
      <div className="product-preview__window" aria-hidden="true">
        <div className="product-preview__bar">
          <span />
          <span />
          <span />
          <p>app.sabinolabs.dev/painel</p>
        </div>

        <div className="product-preview__app">
          <div className="product-preview__side">
            <span className="product-preview__logo">
              <IconStock size={14} />
            </span>
            {[IconDashboard, IconOrders, IconProducts, IconStock, IconUsers].map((Icon, i) => (
              <span key={i} className="product-preview__nav" data-active={i === 0 || undefined}>
                <Icon size={14} />
              </span>
            ))}
          </div>

          <div className="product-preview__main">
            <div className="product-preview__kpis">
              {kpis.map((kpi) => (
                <div key={kpi.label} className="product-preview__kpi" data-hue={kpi.hue}>
                  <span className="product-preview__dot" />
                  <p className="product-preview__kpi-label">{kpi.label}</p>
                  <p className="product-preview__kpi-value">
                    {kpi.value}
                    <span>{kpi.delta}</span>
                  </p>
                </div>
              ))}
            </div>

            <div className="product-preview__grid">
              <div className="product-preview__chart">
                <p className="product-preview__title">{t.dashboard.ordersPerDay}</p>
                <svg viewBox={`0 0 ${largura} ${altura}`} preserveAspectRatio="none">
                  <defs>
                    <linearGradient id="preview-a" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--series)" stopOpacity="0.35" />
                      <stop offset="100%" stopColor="var(--series)" stopOpacity="0" />
                    </linearGradient>
                  </defs>
                  <path d={`${linhaA} L ${largura},${altura} L 0,${altura} Z`} fill="url(#preview-a)" />
                  <path d={linhaA} className="product-preview__line" />
                  <path d={linhaB} className="product-preview__line product-preview__line--b" />
                </svg>
              </div>

              <div className="product-preview__donut">
                <p className="product-preview__title">{t.dashboard.byStatus}</p>
                <svg viewBox="0 0 100 100">
                  <g transform="rotate(-90 50 50)">
                    <circle cx="50" cy="50" r="38" stroke="var(--warning)" strokeDasharray="60 240" />
                    <circle cx="50" cy="50" r="38" stroke="var(--info)" strokeDasharray="56 240" strokeDashoffset="-62" />
                    <circle cx="50" cy="50" r="38" stroke="var(--serious)" strokeDasharray="40 240" strokeDashoffset="-120" />
                    <circle cx="50" cy="50" r="38" stroke="var(--good)" strokeDasharray="56 240" strokeDashoffset="-162" />
                    <circle cx="50" cy="50" r="38" stroke="var(--critical)" strokeDasharray="18 240" strokeDashoffset="-220" />
                  </g>
                  <text x="50" y="56" textAnchor="middle">128</text>
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="product-preview__float product-preview__float--a" aria-hidden="true">
        <span className="badge" data-status="delivered">
          {t.status.delivered}
        </span>
        <strong>PED-000142</strong>
      </div>
      <div className="product-preview__float product-preview__float--b" aria-hidden="true">
        <span className="product-preview__float-icon">
          <IconStock size={16} />
        </span>
        <div>
          <p>{t.dashboard.reservedUnits}</p>
          <strong>64</strong>
        </div>
      </div>
    </figure>
  )
}
