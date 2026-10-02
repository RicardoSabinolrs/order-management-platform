import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { StockPage } from '@/features/stock/pages/StockPage'
import { storeToken } from '@/shared/api/client'
import { renderWithProviders } from '@/test/render'

describe('StockPage', () => {
  it('mostra saldo, reserva e disponivel', async () => {
    storeToken('mock.access.token')
    renderWithProviders(<StockPage />)

    const table = await screen.findByRole('table')
    const linha = within(table).getByText('CAF-500').closest('tr')!
    const celulas = within(linha).getAllByRole('cell')

    // em maos | reservado | disponivel
    expect(celulas[1]).toHaveTextContent('120')
    expect(celulas[2]).toHaveTextContent('0')
    expect(celulas[3]).toHaveTextContent('120')
  })

  it('registra entrada de mercadoria', async () => {
    storeToken('mock.access.token')
    const user = userEvent.setup()
    renderWithProviders(<StockPage />)

    const table = await screen.findByRole('table')
    const linha = within(table).getByText('CAF-500').closest('tr')!
    await user.click(within(linha).getByRole('button', { name: 'Entrada' }))

    await user.type(screen.getByLabelText('Quantidade recebida'), '30')
    await user.click(screen.getByRole('button', { name: 'Confirmar' }))

    await waitFor(() => {
      expect(screen.getByRole('table')).toHaveTextContent('150')
    })
  })
})
