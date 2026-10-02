import { useCallback, useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/features/auth/hooks/useAuth'
import type { Dictionary } from '@/shared/i18n/locales/pt-BR'
import { useI18n } from '@/shared/i18n/useI18n'
import { useDismiss } from '@/shared/lib/useDismiss'
import { Avatar } from '@/shared/ui/Avatar'
import {
  IconChevronDown,
  IconDashboard,
  IconExpand,
  IconHealth,
  IconLogout,
  IconMenu,
  IconOrders,
  IconProducts,
  IconShrink,
  IconStock,
  IconUsers,
} from '@/shared/ui/icons'
import { LanguageSwitcher } from '@/shared/ui/LanguageSwitcher'
import { MockBadge } from '@/shared/ui/MockBadge'
import { ThemeToggle } from '@/shared/ui/ThemeToggle'

type PageKey = keyof Dictionary['pages']
type NavKey = keyof Dictionary['nav']

interface NavItem {
  to: string
  page: PageKey
  label: NavKey
  icon: typeof IconDashboard
  end: boolean
}

interface NavSection {
  title: NavKey
  items: NavItem[]
  /** Secao visivel so para administradores. */
  adminOnly?: boolean
}

const NAV_SECTIONS: NavSection[] = [
  {
    title: 'sectionMenu',
    items: [{ to: '/painel', page: 'dashboard', label: 'dashboard', icon: IconDashboard, end: true }],
  },
  {
    title: 'sectionOperation',
    items: [
      { to: '/pedidos', page: 'orders', label: 'orders', icon: IconOrders, end: false },
      { to: '/produtos', page: 'products', label: 'products', icon: IconProducts, end: false },
      { to: '/estoque', page: 'stock', label: 'stock', icon: IconStock, end: false },
    ],
  },
  {
    title: 'sectionAdmin',
    adminOnly: true,
    items: [{ to: '/usuarios', page: 'users', label: 'users', icon: IconUsers, end: false }],
  },
  {
    title: 'sectionSystem',
    items: [{ to: '/saude', page: 'health', label: 'health', icon: IconHealth, end: false }],
  },
]

// Rota -> cabecalho. A de detalhe (/pedidos/:id) herda o da lista.
const PAGE_BY_PATH: Record<string, PageKey> = Object.fromEntries(
  NAV_SECTIONS.flatMap((secao) => secao.items.map((item) => [item.to, item.page])),
)

// Abaixo desta largura a barra lateral vira gaveta sobre o conteudo.
const TELA_ESTREITA = '(max-width: 900px)'
const CHAVE_RECOLHIDA = 'oms:sidebar-recolhida'

// O armazenamento pode estar bloqueado (janela privada, politica do
// navegador): a preferencia e conveniencia, nunca motivo para quebrar a tela.
function lerRecolhida(): boolean {
  try {
    return localStorage.getItem(CHAVE_RECOLHIDA) === 'true'
  } catch {
    return false
  }
}

function gravarRecolhida(valor: boolean): void {
  try {
    localStorage.setItem(CHAVE_RECOLHIDA, String(valor))
  } catch {
    // sem persistencia, segue so na sessao
  }
}

function useTelaCheia() {
  const [ativa, setAtiva] = useState(() => Boolean(document.fullscreenElement))

  useEffect(() => {
    const sincronizar = () => setAtiva(Boolean(document.fullscreenElement))
    document.addEventListener('fullscreenchange', sincronizar)
    return () => document.removeEventListener('fullscreenchange', sincronizar)
  }, [])

  const alternar = () => {
    if (document.fullscreenElement) void document.exitFullscreen()
    else void document.documentElement.requestFullscreen()
  }

  return { disponivel: Boolean(document.fullscreenEnabled), ativa, alternar }
}

function UserMenu() {
  const { user, signOut } = useAuth()
  const { t } = useI18n()
  const [aberto, setAberto] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  const fechar = useCallback(() => setAberto(false), [])
  useDismiss(ref, aberto, fechar)

  if (!user) return null

  return (
    <div className="popover user-menu" ref={ref}>
      <button
        type="button"
        className="user-chip"
        aria-haspopup="menu"
        aria-expanded={aberto}
        aria-label={t.topbar.userMenu}
        onClick={() => setAberto((atual) => !atual)}
      >
        <Avatar name={user.name} src={user.avatarUrl} size={38} ring />
        <span className="user-chip__text">
          <span className="user-chip__name">{user.name}</span>
          <span className="user-chip__role">{t.roles[user.role]}</span>
        </span>
        <IconChevronDown size={15} />
      </button>

      {aberto ? (
        <div className="popover__panel popover__panel--end user-menu__panel" role="menu">
          <div className="user-menu__head">
            <Avatar name={user.name} src={user.avatarUrl} size={44} />
            <div className="user-menu__who">
              <p className="user-menu__caption">{t.topbar.signedInAs}</p>
              <p className="user-menu__name">{user.name}</p>
              <p className="user-menu__email">{user.email}</p>
            </div>
          </div>
          <button type="button" role="menuitem" className="popover__item popover__item--danger" onClick={signOut}>
            <IconLogout size={16} />
            <span className="popover__label">{t.topbar.signOut}</span>
          </button>
        </div>
      ) : null}
    </div>
  )
}

export function AppLayout() {
  const { user } = useAuth()
  const { t, format } = useI18n()
  const { pathname } = useLocation()
  const telaCheia = useTelaCheia()

  const [recolhida, setRecolhida] = useState(lerRecolhida)
  const [gavetaAberta, setGavetaAberta] = useState(false)

  // Navegar fecha a gaveta: no celular ela cobre o conteudo que se quer ver.
  useEffect(() => {
    setGavetaAberta(false)
  }, [pathname])

  function alternarMenu() {
    if (window.matchMedia(TELA_ESTREITA).matches) {
      setGavetaAberta((aberta) => !aberta)
      return
    }
    setRecolhida((atual) => {
      gravarRecolhida(!atual)
      return !atual
    })
  }

  const pagina = PAGE_BY_PATH[pathname] ?? PAGE_BY_PATH[`/${pathname.split('/')[1] ?? ''}`]
  const meta = pagina ? t.pages[pagina] : undefined
  const primeiroNome = user?.name.split(' ')[0] ?? ''
  const agora = new Date()
  const hora = agora.getHours()
  const saudacao =
    hora < 12 ? t.topbar.goodMorning : hora < 18 ? t.topbar.goodAfternoon : t.topbar.goodEvening

  const secoes = NAV_SECTIONS.filter((secao) => !secao.adminOnly || user?.role === 'admin')

  return (
    <div className="shell" data-collapsed={recolhida} data-drawer={gavetaAberta}>
      <a className="skip-link" href="#conteudo">
        {t.nav.skipToContent}
      </a>

      <aside className="sidebar" id="navegacao">
        <NavLink to="/painel" className="brand">
          <span className="brand__mark" aria-hidden="true">
            <IconStock size={18} />
          </span>
          <span className="brand__text">
            <span className="brand__name">Order Management</span>
            <span className="brand__env">Sabino Labs</span>
          </span>
        </NavLink>

        <nav className="nav" aria-label={t.nav.mainNavigation}>
          {secoes.map((secao) => (
            <div key={secao.title} className="nav__group">
              <p className="nav__section">{t.nav[secao.title]}</p>
              {secao.items.map(({ to, label, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  title={recolhida ? t.nav[label] : undefined}
                  className={({ isActive }) => (isActive ? 'nav__link is-active' : 'nav__link')}
                >
                  <Icon size={18} />
                  <span className="nav__label">{t.nav[label]}</span>
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
      </aside>

      {gavetaAberta ? (
        <button
          type="button"
          className="shell__scrim"
          aria-label={t.nav.closeMenu}
          onClick={() => setGavetaAberta(false)}
        />
      ) : null}

      <div className="main">
        <header className="topbar">
          <div className="topbar__lead">
            <button
              type="button"
              className="icon-btn"
              aria-label={recolhida ? t.nav.expandMenu : t.nav.collapseMenu}
              aria-controls="navegacao"
              onClick={alternarMenu}
            >
              <IconMenu size={20} />
            </button>
            <div className="topbar__heading">
              <p className="topbar__greeting">
                {saudacao}
                {primeiroNome ? `, ${primeiroNome}` : ''}
              </p>
              <p className="topbar__date">{format.today(agora)}</p>
            </div>
          </div>

          <div className="topbar__actions">
            <MockBadge />
            <LanguageSwitcher compact />
            <ThemeToggle />
            {telaCheia.disponivel ? (
              <button
                type="button"
                className="icon-btn topbar__fullscreen"
                aria-label={telaCheia.ativa ? t.topbar.exitFullscreen : t.topbar.fullscreen}
                onClick={telaCheia.alternar}
              >
                {telaCheia.ativa ? <IconShrink size={18} /> : <IconExpand size={18} />}
              </button>
            ) : null}
            <span className="topbar__divider" aria-hidden="true" />
            <UserMenu />
          </div>
        </header>

        <main className="content" id="conteudo">
          {/* O painel abre com o proprio banner, que ja faz o papel de titulo. */}
          {meta && pagina !== 'dashboard' ? (
            <div className="page-head">
              <h1 className="page-head__title">{meta.title}</h1>
              <p className="page-head__subtitle">{meta.subtitle}</p>
            </div>
          ) : null}
          <Outlet />
        </main>
      </div>
    </div>
  )
}
