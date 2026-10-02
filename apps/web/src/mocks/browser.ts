/** Worker do MSW usado no navegador (desenvolvimento). */

import { setupWorker } from 'msw/browser'

import { handlers } from '@/mocks/handlers'

export const worker = setupWorker(...handlers)
