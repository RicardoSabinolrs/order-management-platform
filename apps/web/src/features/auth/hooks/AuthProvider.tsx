import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { fetchCurrentUser, login as loginRequest } from '@/features/auth/api/auth'
import { AuthContext, type AuthContextValue } from '@/features/auth/hooks/authContext'
import type { AuthenticatedUser, Credentials } from '@/features/auth/types'
import { clearStoredToken, getStoredToken, storeToken } from '@/shared/api/client'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthenticatedUser | null>(null)
  const [isRestoring, setIsRestoring] = useState(() => getStoredToken() !== null)

  // Um token no localStorage nao garante sessao valida: ele pode ter expirado
  // enquanto a aba estava fechada. Confirmamos com a API antes de confiar.
  useEffect(() => {
    if (getStoredToken() === null) {
      setIsRestoring(false)
      return
    }

    let cancelled = false
    fetchCurrentUser()
      .then((restored) => {
        if (!cancelled) setUser(restored)
      })
      .catch(() => {
        if (!cancelled) clearStoredToken()
      })
      .finally(() => {
        if (!cancelled) setIsRestoring(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const signIn = useCallback(async (credentials: Credentials) => {
    const { accessToken, user: authenticated } = await loginRequest(credentials)
    storeToken(accessToken)
    setUser(authenticated)
  }, [])

  const signOut = useCallback(() => {
    clearStoredToken()
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: user !== null, isRestoring, signIn, signOut }),
    [user, isRestoring, signIn, signOut],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
