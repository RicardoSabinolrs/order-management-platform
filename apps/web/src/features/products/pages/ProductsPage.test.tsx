import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { ProductsPage } from '@/features/products/pages/ProductsPage'
import { storeToken } from '@/shared/api/client'
import { renderWithProviders } from '@/test/render'

function autenticado() {
  storeToken('mock.access.token')
}

describe('ProductsPage', () => {
  it('lista o catalogo', async () => {
    autenticado()
    renderWithProviders(<ProductsPage />)

    expect(await screen.findByText('Cafe torrado e moido 500g')).toBeInTheDocument()
  })

  it('cadastra um produto novo', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<ProductsPage />)
    await screen.findByRole('table')

    await user.click(screen.getByRole('button', { name: 'Novo produto' }))
    await user.type(screen.getByLabelText('SKU'), 'NOV-001')
    await user.type(screen.getByLabelText('Nome'), 'Produto novo')
    await user.type(screen.getByLabelText('Preço (R$)'), '19,90')
    await user.click(screen.getByRole('button', { name: 'Cadastrar' }))

    await waitFor(() => {
      expect(screen.getByRole('table')).toHaveTextContent('Produto novo')
    })
  })

  it('recusa SKU fora do formato antes de chamar a API', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<ProductsPage />)
    await screen.findByRole('table')

    await user.click(screen.getByRole('button', { name: 'Novo produto' }))
    await user.type(screen.getByLabelText('SKU'), 'ab')
    await user.type(screen.getByLabelText('Nome'), 'Qualquer')
    await user.type(screen.getByLabelText('Preço (R$)'), '10')
    await user.click(screen.getByRole('button', { name: 'Cadastrar' }))

    expect(await screen.findByText(/3 a 32 caracteres/)).toBeInTheDocument()
  })

  it('mostra o erro de SKU duplicado vindo da API', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<ProductsPage />)
    await screen.findByRole('table')

    await user.click(screen.getByRole('button', { name: 'Novo produto' }))
    await user.type(screen.getByLabelText('SKU'), 'CAF-500')
    await user.type(screen.getByLabelText('Nome'), 'Cafe repetido')
    await user.type(screen.getByLabelText('Preço (R$)'), '10')
    await user.click(screen.getByRole('button', { name: 'Cadastrar' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('CAF-500')
  })

  it('desativa um produto', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<ProductsPage />)

    const table = await screen.findByRole('table')
    const linha = within(table).getByText('CAF-500').closest('tr')!

    await user.click(within(linha).getByRole('button', { name: 'Desativar' }))

    await waitFor(() => {
      expect(within(linha).getByText('inativo')).toBeInTheDocument()
    })
  })
})
