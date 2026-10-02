/** Servidor do MSW usado nos testes (Node). */

import { setupServer } from 'msw/node'

import { handlers } from '@/mocks/handlers'

export const server = setupServer(...handlers)
