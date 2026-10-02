import { createContext } from 'react'

import type { AuthenticatedUser, Credentials } from '@/features/auth/types'

export interface AuthContextValue {
  user: AuthenticatedUser | null
  isAuthenticated: boolean
  /** `true` enquanto a sessao guardada ainda esta sendo revalidada. */
  isRestoring: boolean
  signIn: (credentials: Credentials) => Promise<void>
  signOut: () => void
}

/**
 * Em arquivo separado do provider de proposito: um modulo que exporta
 * componente e valor nao-componente quebra o fast refresh do Vite.
 */
export const AuthContext = createContext<AuthContextValue | null>(null)
