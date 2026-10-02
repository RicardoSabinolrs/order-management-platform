import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  createProduct,
  deleteProduct,
  fetchProducts,
  updateProduct,
} from '@/features/products/api/products'
import type { ProductDraft, ProductFilters, ProductPatch } from '@/features/products/types'

/** Chaves centralizadas: invalidar a chave errada e a origem de tela desatualizada. */
export const productKeys = {
  all: ['products'] as const,
  list: (filters: ProductFilters) => [...productKeys.all, 'list', filters] as const,
}

export function useProducts(filters: ProductFilters) {
  return useQuery({
    queryKey: productKeys.list(filters),
    queryFn: () => fetchProducts(filters),
    // Mantem a pagina anterior visivel enquanto a proxima carrega.
    placeholderData: (previous) => previous,
  })
}

function useInvalidateProducts() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: productKeys.all })
    // O estoque nasce junto com o produto: a tela de saldos tambem envelhece.
    void queryClient.invalidateQueries({ queryKey: ['stock'] })
  }
}

export function useCreateProduct() {
  const invalidate = useInvalidateProducts()
  return useMutation({
    mutationFn: (draft: ProductDraft) => createProduct(draft),
    onSuccess: invalidate,
  })
}

export function useUpdateProduct() {
  const invalidate = useInvalidateProducts()
  return useMutation({
    mutationFn: ({ productId, patch }: { productId: string; patch: ProductPatch }) =>
      updateProduct(productId, patch),
    onSuccess: invalidate,
  })
}

export function useDeleteProduct() {
  const invalidate = useInvalidateProducts()
  return useMutation({
    mutationFn: (productId: string) => deleteProduct(productId),
    onSuccess: invalidate,
  })
}
