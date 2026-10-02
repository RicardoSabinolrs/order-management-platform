import type { OrderStatus, OrderSummary } from '@/features/orders/types'

export interface StatusCount {
  status: OrderStatus
  count: number
}

export interface LowStockItem {
  productId: string
  sku: string
  quantityAvailable: number
  quantityReserved: number
}

export interface DailyPoint {
  date: string
  orders: number
  revenueInCents: number
}

export interface DashboardOverview {
  ordersTotal: number
  ordersOpen: number
  ordersByStatus: StatusCount[]
  revenueInCents: number
  averageTicketInCents: number
  productsTotal: number
  productsActive: number
  unitsOnHand: number
  unitsReserved: number
  outOfStock: number
  lowStock: LowStockItem[]
  daily: DailyPoint[]
  recentOrders: OrderSummary[]
}
