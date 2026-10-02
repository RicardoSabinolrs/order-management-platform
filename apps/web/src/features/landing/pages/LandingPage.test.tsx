import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { LandingPage } from '@/features/landing/pages/LandingPage'
import { renderWithProviders } from '@/test/render'

describe('LandingPage', () => {
  it('apresenta o produto e leva ao login', () => {
    renderWithProviders(<LandingPage />)

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('sempre em sincronia')
    expect(screen.getAllByRole('link', { name: /Entrar/ })[0]).toHaveAttribute('href', '/login')
  })

  it.each([
    ['en', 'always in sync', 'Sign in'],
    ['es', 'siempre sincronizados', 'Iniciar sesión'],
  ] as const)('abre direto em %s', (locale, titulo, entrar) => {
    renderWithProviders(<LandingPage />, { locale })

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent(titulo)
    expect(screen.getAllByRole('link', { name: entrar }).length).toBeGreaterThan(0)
  })

  it('troca de idioma pelo menu e lembra a escolha', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LandingPage />)

    await user.click(screen.getByRole('button', { name: /Idioma/ }))
    await user.click(screen.getByRole('menuitemradio', { name: /English/ }))

    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('always in sync')
    expect(document.documentElement.lang).toBe('en')
    expect(localStorage.getItem('oms:idioma')).toBe('en')
  })

  it('alterna entre tema claro e escuro', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LandingPage />)

    const antes = document.documentElement.dataset.theme
    await user.click(screen.getByRole('button', { name: /Mudar para o tema/ }))
    const depois = document.documentElement.dataset.theme

    expect(depois).not.toBe(antes)
    expect(localStorage.getItem('oms:tema')).toBe(depois)
  })
})
