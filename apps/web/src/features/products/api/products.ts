import type { Product, ProductDraft, ProductFilters, ProductPatch } from '@/features/products/types'
import { api } from '@/shared/api/client'
import type { PageDTO, ProductDTO } from '@/shared/api/types'
import type { Page } from '@/shared/api/page'
import { toPage } from '@/shared/api/page'

function toProduct(dto: ProductDTO): Product {
  return {
    id: dto.id,
    sku: dto.sku,
    name: dto.name,
    description: dto.description,
    priceInCents: dto.price_in_cents,
    currency: dto.currency,
    active: dto.active,
    updatedAt: dto.updated_at,
  }
}

export async function fetchProducts(filters: ProductFilters): Promise<Page<Product>> {
  const params = new URLSearchParams({ page: String(filters.page), page_size: '10' })
  if (filters.search.trim()) params.set('search', filters.search.trim())
  if (filters.active !== null) params.set('active', String(filters.active))

  const page = await api.get<PageDTO<ProductDTO>>(`/api/v1/products?${params.toString()}`)
  return toPage(page, toProduct)
}

export async function fetchProduct(productId: string): Promise<Product> {
  return toProduct(await api.get<ProductDTO>(`/api/v1/products/${productId}`))
}

export async function createProduct(draft: ProductDraft): Promise<Product> {
  const dto = await api.post<ProductDTO>('/api/v1/products', {
    sku: draft.sku,
    name: draft.name,
    description: draft.description,
    price_in_cents: draft.priceInCents,
    initial_stock: draft.initialStock,
  })
  return toProduct(dto)
}

export async function updateProduct(productId: string, patch: ProductPatch): Promise<Product> {
  // Somente os campos presentes vao no PATCH: enviar `undefined` explicito
  // faria o backend recusar o payload (`extra="forbid"` nao, mas o contrato
  // ficaria ambiguo entre "nao mudar" e "limpar").
  const body: Record<string, unknown> = {}
  if (patch.name !== undefined) body.name = patch.name
  if (patch.description !== undefined) body.description = patch.description
  if (patch.priceInCents !== undefined) body.price_in_cents = patch.priceInCents
  if (patch.active !== undefined) body.active = patch.active

  return toProduct(await api.patch<ProductDTO>(`/api/v1/products/${productId}`, body))
}

export async function deleteProduct(productId: string): Promise<void> {
  await api.delete<void>(`/api/v1/products/${productId}`)
}
