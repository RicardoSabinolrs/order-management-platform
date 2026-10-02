import { useContext } from 'react'

import { AuthContext, type AuthContextValue } from '@/features/auth/hooks/authContext'

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error('useAuth precisa estar dentro de <AuthProvider>.')
  }
  return context
}
