import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { LoginPage } from '@/features/auth/pages/LoginPage'
import { DEMO_CREDENTIALS } from '@/mocks/data'
import { getStoredToken } from '@/shared/api/client'
import { renderWithProviders } from '@/test/render'

describe('LoginPage', () => {
  it('valida os campos antes de chamar a API', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('Informe o e-mail.')).toBeInTheDocument()
    expect(screen.getByText('Informe a senha.')).toBeInTheDocument()
    expect(getStoredToken()).toBeNull()
  })

  it('recusa e-mail em formato invalido', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.type(screen.getByLabelText('E-mail'), 'nao-e-um-email')
    await user.type(screen.getByLabelText('Senha'), 'demo1234')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByText('E-mail em formato inválido.')).toBeInTheDocument()
  })

  it('guarda o token quando as credenciais estao corretas', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.type(screen.getByLabelText('E-mail'), DEMO_CREDENTIALS.email)
    await user.type(screen.getByLabelText('Senha'), DEMO_CREDENTIALS.password)
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    await waitFor(() => {
      expect(getStoredToken()).toBe('mock.access.token')
    })
  })

  it('mostra a mensagem da API quando as credenciais estao erradas', async () => {
    const user = userEvent.setup()
    renderWithProviders(<LoginPage />)

    await user.type(screen.getByLabelText('E-mail'), DEMO_CREDENTIALS.email)
    await user.type(screen.getByLabelText('Senha'), 'senha-errada')
    await user.click(screen.getByRole('button', { name: 'Entrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('E-mail ou senha incorretos.')
    expect(getStoredToken()).toBeNull()
  })
})
