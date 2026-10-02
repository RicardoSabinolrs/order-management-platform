import { screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { storeToken } from '@/shared/api/client'
import { renderWithProviders } from '@/test/render'

function autenticado() {
  storeToken('mock.access.token')
}

describe('DashboardPage', () => {
  it('mostra os indicadores de pedidos e estoque', async () => {
    autenticado()
    renderWithProviders(<DashboardPage />)

    // Dentro da regiao de indicadores: "Faturamento" tambem e o nome de um
    // botao do grafico, e a busca global pegaria os dois.
    const indicadores = await screen.findByRole('region', { name: 'Indicadores' })

    expect(within(indicadores).getByText('Pedidos em aberto')).toBeInTheDocument()
    expect(within(indicadores).getByText('Faturamento')).toBeInTheDocument()
    expect(within(indicadores).getByText('Ticket médio')).toBeInTheDocument()
    expect(within(indicadores).getByText('Unidades reservadas')).toBeInTheDocument()
    expect(within(indicadores).getByText('Produtos sem saldo')).toBeInTheDocument()
  })

  it('lista cada status de pedido na legenda da rosca', async () => {
    autenticado()
    renderWithProviders(<DashboardPage />)

    const painel = (await screen.findByText('Pedidos por status')).closest('section')!
    const linhas = within(painel).getAllByRole('listitem')

    expect(linhas).toHaveLength(5)
    expect(within(painel).getByText('Aguardando')).toBeInTheDocument()
    expect(within(painel).getByText('Cancelado')).toBeInTheDocument()
  })

  it('descreve a rosca para tecnologia assistiva', async () => {
    autenticado()
    renderWithProviders(<DashboardPage />)

    // A cor nunca carrega significado sozinha: a rosca tem rotulo textual e a
    // legenda repete cada fatia por extenso.
    expect(await screen.findByRole('img', { name: /^Distribuição de \d+ pedidos$/ })).toBeInTheDocument()
  })

  it('plota a serie diaria e permite trocar a medida', async () => {
    autenticado()
    const user = userEvent.setup()
    renderWithProviders(<DashboardPage />)

    expect(await screen.findByRole('img', { name: /pedidos nos últimos 14 dias/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Faturamento' }))

    expect(
      await screen.findByRole('img', { name: /faturamento nos últimos 14 dias/i }),
    ).toBeInTheDocument()
  })

  it('lista os pedidos mais recentes com link para o detalhe', async () => {
    autenticado()
    renderWithProviders(<DashboardPage />)

    const painel = (await screen.findByText('Pedidos recentes')).closest('section')!
    const linhas = within(painel).getAllByRole('row')

    expect(linhas).toHaveLength(6) // 5 pedidos + cabecalho
    expect(within(painel).getByRole('link', { name: 'PED-000001' })).toHaveAttribute(
      'href',
      '/pedidos/ord_0001',
    )
  })

  it('avisa quando nada esta em nivel critico', async () => {
    autenticado()
    renderWithProviders(<DashboardPage />)

    // O catalogo de demonstracao tem o moedor com 12 unidades: acima do limite
    // de 10, entao a lista de reposicao vem vazia.
    expect(await screen.findByText('Nenhum produto em nível crítico.')).toBeInTheDocument()
  })
})
