import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { OrdersPage } from '@/features/orders/pages/OrdersPage'
import { storeToken } from '@/shared/api/client'
import { renderWithProviders } from '@/test/render'

function autenticado() {
  storeToken('mock.access.token')
}

describe('OrdersPage', () => {
  it('lista os pedidos da primeira pagina', async () => {
    autenticado()
    renderWithProviders(<OrdersPage />)

    const table = await screen.findByRole('table')
    await waitFor(() => {
      // 10 por pagina + cabecalho.
      expect(within(table).getAllByRole('row')).toHaveLength(11)
    })
  })

  it('filtra por status', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<OrdersPage />)
    await screen.findByRole('table')

    await user.click(screen.getByRole('button', { name: 'Cancelado' }))

    await waitFor(() => {
      const table = screen.getByRole('table')
      expect(within(table).getAllByText('Cancelado').length).toBeGreaterThan(0)
      expect(within(table).queryByText('Entregue')).not.toBeInTheDocument()
    })
  })

  it('avisa quando a busca nao encontra nada', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<OrdersPage />)
    await screen.findByRole('table')

    await user.type(
      screen.getByPlaceholderText('Buscar por referência ou cliente'),
      'cliente-inexistente',
    )

    expect(await screen.findByText('Nenhum pedido encontrado.')).toBeInTheDocument()
  })

  it('cria um pedido pelo formulario', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<OrdersPage />)
    await screen.findByRole('table')

    await user.click(screen.getByRole('button', { name: 'Novo pedido' }))

    await user.type(screen.getByLabelText('Cliente'), 'Joana Prado')
    await user.type(screen.getByLabelText('E-mail'), 'joana@exemplo.com')

    const quantidade = await screen.findByLabelText('Quantidade de Cafe torrado e moido 500g')
    await user.clear(quantidade)
    await user.type(quantidade, '2')

    await user.click(screen.getByRole('button', { name: 'Criar pedido' }))

    await waitFor(() => {
      expect(screen.getByRole('table')).toHaveTextContent('Joana Prado')
    })
  })

  it('exige cliente e item antes de enviar', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<OrdersPage />)
    await screen.findByRole('table')

    await user.click(screen.getByRole('button', { name: 'Novo pedido' }))
    await user.click(screen.getByRole('button', { name: 'Criar pedido' }))

    expect(await screen.findByText('Informe o nome do cliente.')).toBeInTheDocument()
    expect(screen.getByText('Escolha ao menos um produto.')).toBeInTheDocument()
  })
})
