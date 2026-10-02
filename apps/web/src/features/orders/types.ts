export const ORDER_STATUSES = [
  'pending',
  'confirmed',
  'shipped',
  'delivered',
  'cancelled',
] as const

export type OrderStatus = (typeof ORDER_STATUSES)[number]

/** Espelha ALLOWED_TRANSITIONS do backend: a interface so oferece o possivel. */
export const ALLOWED_TRANSITIONS: Record<OrderStatus, OrderStatus[]> = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['shipped', 'cancelled'],
  shipped: ['delivered'],
  delivered: [],
  cancelled: [],
}

export interface OrderItem {
  productId: string
  sku: string
  description: string
  quantity: number
  unitPriceInCents: number
  subtotalInCents: number
}

export interface Order {
  id: string
  reference: string
  status: OrderStatus
  customer: { name: string; email: string }
  items: OrderItem[]
  totalInCents: number
  cancellationReason: string | null
  placedAt: string
  updatedAt: string
}

export interface OrderSummary {
  id: string
  reference: string
  status: OrderStatus
  customerName: string
  itemCount: number
  totalInCents: number
  placedAt: string
}

export interface OrderDraft {
  customer: { name: string; email: string }
  items: { productId: string; quantity: number }[]
}

export interface OrderFilters {
  status: OrderStatus | 'all'
  search: string
  page: number
}
