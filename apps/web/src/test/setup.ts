import '@testing-library/jest-dom/vitest'

import { afterAll, afterEach, beforeAll } from 'vitest'

import { resetDemoData } from '@/mocks/data'
import { server } from '@/mocks/server'

// Os testes usam os mesmos handlers do navegador: a API se comporta de um
// jeito so, definido em um lugar so.
beforeAll(() => {
  server.listen({ onUnhandledFrame: 'error' })
})

afterEach(() => {
  server.resetHandlers()
  // Os handlers mutam os dados (reserva, baixa): sem reset, um teste veria o
  // estoque que o anterior consumiu.
  resetDemoData()
  localStorage.clear()
})

afterAll(() => {
  server.close()
})
