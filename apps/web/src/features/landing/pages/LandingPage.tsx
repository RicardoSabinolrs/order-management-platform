import { Link } from 'react-router-dom'

import { useAuth } from '@/features/auth/hooks/useAuth'
import { ProductPreview } from '@/features/landing/components/ProductPreview'
import { useI18n } from '@/shared/i18n/useI18n'
import {
  IconArrowRight,
  IconBolt,
  IconChart,
  IconRefresh,
  IconShield,
  IconStock,
  IconUsers,
} from '@/shared/ui/icons'
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher'
import { ThemeToggle } from '@/shared/ui/ThemeToggle'

// Um icone por recurso, na mesma ordem do dicionario.
const FEATURE_ICONS = [IconShield, IconRefresh, IconStock, IconChart, IconUsers, IconBolt]
const FEATURE_HUES = ['violet', 'blue', 'orange', 'pink', 'teal', 'blue'] as const

export function LandingPage() {
  const { t } = useI18n()
  const { isAuthenticated } = useAuth()

  // Quem ja tem sessao vai direto ao painel; quem nao tem, ao login.
  const destino = isAuthenticated ? '/painel' : '/login'
  const acao = isAuthenticated ? t.landing.openDashboard : t.landing.signIn

  const stats = [
    { value: t.landing.statsReservationValue, label: t.landing.statsReservation },
    { value: t.landing.statsLanguagesValue, label: t.landing.statsLanguages },
    { value: t.landing.statsUpdateValue, label: t.landing.statsUpdate },
    { value: t.landing.statsThemesValue, label: t.landing.statsThemes },
  ]

  return (
    <div className="landing">
      <header className="landing__header">
        <div className="landing__container landing__header-inner">
          <Link to="/" className="landing__brand">
            <span className="brand__mark" aria-hidden="true">
              <IconStock size={18} />
            </span>
            Order Management
          </Link>

          <nav className="landing__nav" aria-label={t.nav.mainNavigation}>
            <a href="#recursos">{t.landing.navFeatures}</a>
            <a href="#como-funciona">{t.landing.navHow}</a>
            <a href="#perguntas">{t.landing.navFaq}</a>
          </nav>

          <div className="landing__prefs">
            <LanguageSwitcher compact />
            <ThemeToggle />
            <Link className="btn btn--primary landing__cta-sm" to={destino}>
              {acao}
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-hero__bg" aria-hidden="true" />
          <div className="landing__container landing-hero__inner">
            <div className="landing-hero__copy">
              <span className="landing-hero__badge">
                <span className="landing-hero__badge-dot" aria-hidden="true" />
                {t.landing.heroBadge}
              </span>
              <h1 className="landing-hero__title">
                {t.landing.heroTitleStart} <span className="text-gradient">{t.landing.heroTitleHighlight}</span>
              </h1>
              <p className="landing-hero__lede">{t.landing.heroLede}</p>
              <div className="landing-hero__actions">
                <Link className="btn btn--primary btn--lg" to={destino}>
                  {isAuthenticated ? t.landing.openDashboard : t.landing.heroPrimary}
                  <IconArrowRight size={17} />
                </Link>
                <a className="btn btn--secondary btn--lg" href="#recursos">
                  {t.landing.heroSecondary}
                </a>
              </div>
              <p className="landing-hero__note">{t.landing.heroNote}</p>
            </div>

            <ProductPreview />
          </div>
        </section>

        <section className="landing__container landing-stats" aria-label={t.landing.featuresEyebrow}>
          {stats.map((stat) => (
            <div key={stat.label} className="landing-stats__item">
              <p className="landing-stats__value">{stat.value}</p>
              <p className="landing-stats__label">{stat.label}</p>
            </div>
          ))}
        </section>

        <section id="recursos" className="landing-section">
          <div className="landing__container">
            <div className="landing-section__head">
              <p className="landing-section__eyebrow">{t.landing.featuresEyebrow}</p>
              <h2 className="landing-section__title">{t.landing.featuresTitle}</h2>
              <p className="landing-section__lede">{t.landing.featuresLede}</p>
            </div>

            <ul className="feature-grid">
              {t.landing.features.map((feature, index) => {
                const Icon = FEATURE_ICONS[index] ?? IconBolt
                return (
                  <li key={feature.title} className="feature-card">
                    <span className="feature-card__icon" data-hue={FEATURE_HUES[index]} aria-hidden="true">
                      <Icon size={20} />
                    </span>
                    <h3 className="feature-card__title">{feature.title}</h3>
                    <p className="feature-card__text">{feature.text}</p>
                  </li>
                )
              })}
            </ul>
          </div>
        </section>

        <section id="como-funciona" className="landing-section landing-section--tinted">
          <div className="landing__container">
            <div className="landing-section__head">
              <p className="landing-section__eyebrow">{t.landing.howEyebrow}</p>
              <h2 className="landing-section__title">{t.landing.howTitle}</h2>
            </div>
            <ol className="steps">
              {t.landing.steps.map((step, index) => (
                <li key={step.title} className="step">
                  <span className="step__number" aria-hidden="true">
                    {String(index + 1).padStart(2, '0')}
                  </span>
                  <h3 className="step__title">{step.title}</h3>
                  <p className="step__text">{step.text}</p>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="perguntas" className="landing-section">
          <div className="landing__container landing-faq">
            <h2 className="landing-section__title">{t.landing.faqTitle}</h2>
            <div className="landing-faq__list">
              {t.landing.faq.map((item) => (
                <details key={item.q} className="faq-item">
                  <summary>{item.q}</summary>
                  <p>{item.a}</p>
                </details>
              ))}
            </div>
          </div>
        </section>

        <section className="landing__container">
          <div className="landing-cta">
            <div>
              <h2 className="landing-cta__title">{t.landing.ctaTitle}</h2>
              <p className="landing-cta__text">{t.landing.ctaText}</p>
            </div>
            <Link className="btn btn--light btn--lg" to={destino}>
              {isAuthenticated ? t.landing.openDashboard : t.landing.ctaButton}
              <IconArrowRight size={17} />
            </Link>
          </div>
        </section>
      </main>

      <footer className="landing__footer">
        <div className="landing__container landing__footer-inner">
          <p className="landing__brand landing__brand--muted">
            <span className="brand__mark" aria-hidden="true">
              <IconStock size={16} />
            </span>
            Order Management
          </p>
          <p>{t.landing.footer(new Date().getFullYear())}</p>
        </div>
      </footer>
    </div>
  )
}
