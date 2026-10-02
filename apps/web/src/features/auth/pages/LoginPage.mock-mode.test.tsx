import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

// Simula a aplicacao rodando com VITE_USE_MOCKS=true. `vi.mock` e icado para
// o topo, entao o modulo de config ja sobe trocado para todo este arquivo.
vi.mock('@/shared/config/env', () => ({
  config: { apiBaseUrl: '', useMocks: true },
}))

import { DEMO_CREDENTIALS } from '@/features/auth/demo'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { getStoredToken } from '@/shared/api/client'
import { renderWithProviders } from '@/test/render'

describe('LoginPage em modo de demonstracao', () => {
  it('ja vem com e-mail e senha preenchidos', () => {
    renderWithProviders(<LoginPage />)

    expect(screen.getByLabelText('E-mail')).toHaveValue(DEMO_CREDENTIALS.email)
    expect(screen.getByLabelText('Senha')).toHaveValue(DEMO_CREDENTIALS.password)
  })

  it('entra em um clique, sem backend no ar', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => {
      expect(getStoredToken()).toBe('mock.access.token')
    })
  })

  it('avisa que as credenciais estao preenchidas', () => {
    renderWithProviders(<LoginPage />)

    expect(screen.getByText(/já preenchidas/)).toBeInTheDocument()
  })
})
