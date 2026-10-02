import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/app/layouts/AppLayout'
import { ProtectedRoute } from '@/app/routes/ProtectedRoute'
import { LoginPage } from '@/features/auth/pages/LoginPage'
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage'
import { HealthPage } from '@/features/health/pages/HealthPage'
import { LandingPage } from '@/features/landing/pages/LandingPage'
import { OrderDetailPage } from '@/features/orders/pages/OrderDetailPage'
import { OrdersPage } from '@/features/orders/pages/OrdersPage'
import { ProductsPage } from '@/features/products/pages/ProductsPage'
import { StockPage } from '@/features/stock/pages/StockPage'
import { UsersPage } from '@/features/users/pages/UsersPage'

export function App() {
  return (
    <Routes>
      {/* Publico: o site e a entrada. O painel mora em /painel. */}
      <Route index element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="painel" element={<DashboardPage />} />
          <Route path="pedidos" element={<OrdersPage />} />
          <Route path="pedidos/:orderId" element={<OrderDetailPage />} />
          <Route path="produtos" element={<ProductsPage />} />
          <Route path="estoque" element={<StockPage />} />
          <Route path="usuarios" element={<UsersPage />} />
          <Route path="saude" element={<HealthPage />} />
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
