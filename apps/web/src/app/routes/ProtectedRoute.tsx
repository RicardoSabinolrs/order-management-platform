import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { useAuth } from '@/features/auth/hooks/useAuth'
import { SkeletonRows } from '@/shared/ui/Skeleton'

export function ProtectedRoute() {
  const { isAuthenticated, isRestoring } = useAuth()
  const location = useLocation()

  // Sem esta espera, recarregar a pagina jogaria o usuario para o login antes
  // de a sessao guardada terminar de ser revalidada.
  if (isRestoring) {
    return <SkeletonRows rows={3} />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
