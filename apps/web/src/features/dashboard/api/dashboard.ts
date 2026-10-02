import type { DashboardOverview } from '@/features/dashboard/types'
import { api } from '@/shared/api/client'
import type { OrderStatusDTO, OrderSummaryDTO } from '@/shared/api/types'

interface DashboardDTO {
  orders_total: number
  orders_open: number
  orders_by_status: { status: OrderStatusDTO; count: number }[]
  revenue_in_cents: number
  average_ticket_in_cents: number
  products_total: number
  products_active: number
  units_on_hand: number
  units_reserved: number
  out_of_stock: number
  low_stock: {
    product_id: string
    sku: string
    quantity_available: number
    quantity_reserved: number
  }[]
  daily: { date: string; orders: number; revenue_in_cents: number }[]
  recent_orders: OrderSummaryDTO[]
}

export async function fetchOverview(): Promise<DashboardOverview> {
  const dto = await api.get<DashboardDTO>('/api/v1/dashboard')

  return {
    ordersTotal: dto.orders_total,
    ordersOpen: dto.orders_open,
    ordersByStatus: dto.orders_by_status,
    revenueInCents: dto.revenue_in_cents,
    averageTicketInCents: dto.average_ticket_in_cents,
    productsTotal: dto.products_total,
    productsActive: dto.products_active,
    unitsOnHand: dto.units_on_hand,
    unitsReserved: dto.units_reserved,
    outOfStock: dto.out_of_stock,
    lowStock: dto.low_stock.map((item) => ({
      productId: item.product_id,
      sku: item.sku,
      quantityAvailable: item.quantity_available,
      quantityReserved: item.quantity_reserved,
    })),
    daily: dto.daily.map((point) => ({
      date: point.date,
      orders: point.orders,
      revenueInCents: point.revenue_in_cents,
    })),
    recentOrders: dto.recent_orders.map((order) => ({
      id: order.id,
      reference: order.reference,
      status: order.status,
      customerName: order.customer_name,
      itemCount: order.item_count,
      totalInCents: order.total_in_cents,
      placedAt: order.placed_at,
    })),
  }
}
