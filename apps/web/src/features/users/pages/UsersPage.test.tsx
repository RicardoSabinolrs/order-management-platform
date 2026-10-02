import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { UsersPage } from '@/features/users/pages/UsersPage'
import { storeToken } from '@/shared/api/client'
import { renderWithProviders } from '@/test/render'

// Token do mock: o sufixo escolhe o usuario (ver `currentUser` nos handlers).
const ADMIN = 'mock.access.token'
const LEITURA = 'mock.access.token.usr_0003'

describe('UsersPage', () => {
  it('lista a equipe para o administrador, marcando quem esta logado', async () => {
    storeToken(ADMIN)
    renderWithProviders(<UsersPage />)

    const tabela = await screen.findByRole('table')
    expect(within(tabela).getByText('Marina Duarte')).toBeInTheDocument()
    expect(within(tabela).getByText('você')).toBeInTheDocument()
    expect(within(tabela).getByText('Administrador')).toBeInTheDocument()
  })

  it('cadastra um usuario pelo formulario', async () => {
    storeToken(ADMIN)
    const user = userEvent.setup()
    renderWithProviders(<UsersPage />)

    await user.click(await screen.findByRole('button', { name: 'Novo usuário' }))
    const dialogo = screen.getByRole('dialog')
    await user.type(within(dialogo).getByLabelText('Nome'), 'Carla Mendes')
    await user.type(within(dialogo).getByLabelText('E-mail'), 'carla@sabinolabs.dev')
    await user.type(within(dialogo).getByLabelText('Senha'), 'carla12345')
    await user.click(within(dialogo).getByLabelText(/Leitura/))
    await user.click(within(dialogo).getByRole('button', { name: 'Cadastrar usuário' }))

    expect(await screen.findByText('Carla Mendes cadastrado')).toBeInTheDocument()
    expect(await screen.findByRole('cell', { name: 'carla@sabinolabs.dev' })).toBeInTheDocument()
  })

  it('valida os campos antes de chamar a API', async () => {
    storeToken(ADMIN)
    const user = userEvent.setup()
    renderWithProviders(<UsersPage />)

    await user.click(await screen.findByRole('button', { name: 'Novo usuário' }))
    const dialogo = screen.getByRole('dialog')
    await user.type(within(dialogo).getByLabelText('Senha'), 'curta')
    await user.click(within(dialogo).getByRole('button', { name: 'Cadastrar usuário' }))

    expect(within(dialogo).getByText('Informe o nome.')).toBeInTheDocument()
    expect(within(dialogo).getByText('A senha tem no mínimo 8 caracteres.')).toBeInTheDocument()
  })

  it('mostra o conflito de e-mail vindo da API', async () => {
    storeToken(ADMIN)
    const user = userEvent.setup()
    renderWithProviders(<UsersPage />)

    await user.click(await screen.findByRole('button', { name: 'Novo usuário' }))
    const dialogo = screen.getByRole('dialog')
    await user.type(within(dialogo).getByLabelText('Nome'), 'Outra Marina')
    await user.type(within(dialogo).getByLabelText('E-mail'), 'marina.duarte@sabinolabs.dev')
    await user.type(within(dialogo).getByLabelText('Senha'), 'marina99999')
    await user.click(within(dialogo).getByRole('button', { name: 'Cadastrar usuário' }))

    expect(await within(dialogo).findByRole('alert')).toHaveTextContent(/marina.duarte@sabinolabs.dev/)
  })

  it('explica a restricao para quem nao e administrador', async () => {
    storeToken(LEITURA)
    renderWithProviders(<UsersPage />)

    expect(await screen.findByText('Acesso restrito a administradores.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Novo usuário' })).not.toBeInTheDocument()
  })
})
