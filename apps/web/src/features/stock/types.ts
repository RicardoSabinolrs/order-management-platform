export interface StockBalance {
  productId: string
  sku: string
  quantityOnHand: number
  quantityReserved: number
  quantityAvailable: number
  updatedAt: string
}
