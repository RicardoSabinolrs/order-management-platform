export interface Product {
  id: string
  sku: string
  name: string
  description: string
  priceInCents: number
  currency: string
  active: boolean
  updatedAt: string
}

export interface ProductDraft {
  sku: string
  name: string
  description: string
  priceInCents: number
  initialStock: number
}

export interface ProductPatch {
  name?: string
  description?: string
  priceInCents?: number
  active?: boolean
}

export interface ProductFilters {
  search: string
  active: boolean | null
  page: number
}
