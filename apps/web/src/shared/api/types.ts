/**
 * Espelho dos contratos da API (snake_case, como o backend os expoe).
 *
 * As camadas `api/` de cada feature traduzem estes DTOs para os tipos em
 * camelCase que a interface usa. A traducao fica em um lugar so: quando o
 * contrato muda, o compilador aponta exatamente onde.
 */

export interface PageDTO<ItemT> {
  items: ItemT[]
  total: number
  page: number
  page_size: number
}

export interface ProductDTO {
  id: string
  sku: string
  name: string
  description: string
  price_in_cents: number
  currency: string
  active: boolean
  created_at: string
  updated_at: string
}

export interface StockDTO {
  product_id: string
  sku: string
  quantity_on_hand: number
  quantity_reserved: number
  quantity_available: number
  updated_at: string
}

export type OrderStatusDTO = 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled'

export interface OrderItemDTO {
  product_id: string
  sku: string
  description: string
  quantity: number
  unit_price_in_cents: number
  subtotal_in_cents: number
}

export interface OrderDTO {
  id: string
  reference: string
  status: OrderStatusDTO
  customer: { name: string; email: string }
  items: OrderItemDTO[]
  total_in_cents: number
  currency: string
  cancellation_reason: string | null
  placed_at: string
  updated_at: string
}

export interface OrderSummaryDTO {
  id: string
  reference: string
  status: OrderStatusDTO
  customer_name: string
  item_count: number
  total_in_cents: number
  placed_at: string
}

export interface UserDTO {
  id: string
  name: string
  email: string
  role: 'admin' | 'operator' | 'viewer'
  avatar_url: string | null
}

export interface LoginResponseDTO {
  access_token: string
  token_type: 'bearer'
  expires_in: number
  user: UserDTO
}
