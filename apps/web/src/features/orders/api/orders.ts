import type {
  Order,
  OrderDraft,
  OrderFilters,
  OrderSummary,
} from '@/features/orders/types'
import { api } from '@/shared/api/client'
import type { Page } from '@/shared/api/page'
import { toPage } from '@/shared/api/page'
import type { OrderDTO, OrderSummaryDTO, PageDTO } from '@/shared/api/types'

function toOrder(dto: OrderDTO): Order {
  return {
    id: dto.id,
    reference: dto.reference,
    status: dto.status,
    customer: dto.customer,
    items: dto.items.map((item) => ({
      productId: item.product_id,
      sku: item.sku,
      description: item.description,
      quantity: item.quantity,
      unitPriceInCents: item.unit_price_in_cents,
      subtotalInCents: item.subtotal_in_cents,
    })),
    totalInCents: dto.total_in_cents,
    cancellationReason: dto.cancellation_reason,
    placedAt: dto.placed_at,
    updatedAt: dto.updated_at,
  }
}

function toSummary(dto: OrderSummaryDTO): OrderSummary {
  return {
    id: dto.id,
    reference: dto.reference,
    status: dto.status,
    customerName: dto.customer_name,
    itemCount: dto.item_count,
    totalInCents: dto.total_in_cents,
    placedAt: dto.placed_at,
  }
}

export async function fetchOrders(filters: OrderFilters): Promise<Page<OrderSummary>> {
  const params = new URLSearchParams({ page: String(filters.page), page_size: '10' })
  if (filters.status !== 'all') params.set('status', filters.status)
  if (filters.search.trim()) params.set('search', filters.search.trim())

  const page = await api.get<PageDTO<OrderSummaryDTO>>(`/api/v1/orders?${params.toString()}`)
  return toPage(page, toSummary)
}

export async function fetchOrder(orderId: string): Promise<Order> {
  return toOrder(await api.get<OrderDTO>(`/api/v1/orders/${orderId}`))
}

export async function createOrder(draft: OrderDraft): Promise<Order> {
  const dto = await api.post<OrderDTO>('/api/v1/orders', {
    customer: draft.customer,
    items: draft.items.map((item) => ({
      product_id: item.productId,
      quantity: item.quantity,
    })),
  })
  return toOrder(dto)
}

export async function confirmOrder(orderId: string): Promise<Order> {
  return toOrder(await api.post<OrderDTO>(`/api/v1/orders/${orderId}/confirm`))
}

export async function shipOrder(orderId: string): Promise<Order> {
  return toOrder(await api.post<OrderDTO>(`/api/v1/orders/${orderId}/ship`))
}

export async function deliverOrder(orderId: string): Promise<Order> {
  return toOrder(await api.post<OrderDTO>(`/api/v1/orders/${orderId}/deliver`))
}

export async function cancelOrder(orderId: string, reason: string): Promise<Order> {
  return toOrder(await api.post<OrderDTO>(`/api/v1/orders/${orderId}/cancel`, { reason }))
}
