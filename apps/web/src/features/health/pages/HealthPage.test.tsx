import { http, HttpResponse } from 'msw'
import { screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { HealthPage } from '@/features/health/pages/HealthPage'
import { server } from '@/mocks/server'
import { renderWithProviders } from '@/test/render'

describe('HealthPage', () => {
  it('lista as dependencias quando tudo esta no ar', async () => {
    renderWithProviders(<HealthPage />)

    expect(await screen.findByText('postgres')).toBeInTheDocument()
    expect(await screen.findByText('no ar')).toBeInTheDocument()
  })

  it('mostra a dependencia caida a partir do corpo problem+json do 503', async () => {
    // O readiness degradado responde 503: a tela precisa ler o corpo, nao
    // tratar como erro de rede.
    server.use(
      http.get('/health/ready', () =>
        HttpResponse.json(
          {
            type: 'about:blank#dependency_unavailable',
            title: 'DependencyUnavailableError',
            status: 503,
            detail: 'Dependencias indisponiveis: postgres.',
            code: 'dependency_unavailable',
            instance: '/health/ready',
            dependencies: [{ name: 'postgres', healthy: false }],
          },
          { status: 503, headers: { 'Content-Type': 'application/problem+json' } },
        ),
      ),
    )

    renderWithProviders(<HealthPage />)

    expect(await screen.findByText('indisponível')).toBeInTheDocument()
  })
})
