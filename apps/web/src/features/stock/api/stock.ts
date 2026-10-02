import type { StockBalance } from '@/features/stock/types'
import { api } from '@/shared/api/client'
import type { Page } from '@/shared/api/page'
import { toPage } from '@/shared/api/page'
import type { PageDTO, StockDTO } from '@/shared/api/types'

function toBalance(dto: StockDTO): StockBalance {
  return {
    productId: dto.product_id,
    sku: dto.sku,
    quantityOnHand: dto.quantity_on_hand,
    quantityReserved: dto.quantity_reserved,
    quantityAvailable: dto.quantity_available,
    updatedAt: dto.updated_at,
  }
}

export async function fetchStock(page: number): Promise<Page<StockBalance>> {
  const params = new URLSearchParams({ page: String(page), page_size: '10' })
  const result = await api.get<PageDTO<StockDTO>>(`/api/v1/stock?${params.toString()}`)
  return toPage(result, toBalance)
}

export async function receiveStock(productId: string, quantity: number): Promise<StockBalance> {
  return toBalance(
    await api.post<StockDTO>(`/api/v1/stock/${productId}/receipts`, { quantity }),
  )
}

export async function adjustStock(
  productId: string,
  quantityOnHand: number,
  reason: string,
): Promise<StockBalance> {
  return toBalance(
    await api.post<StockDTO>(`/api/v1/stock/${productId}/adjustments`, {
      quantity_on_hand: quantityOnHand,
      reason,
    }),
  )
}
