import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { adjustStock, fetchStock, receiveStock } from '@/features/stock/api/stock'

export const stockKeys = {
  all: ['stock'] as const,
  list: (page: number) => [...stockKeys.all, 'list', page] as const,
}

export function useStock(page: number) {
  return useQuery({
    queryKey: stockKeys.list(page),
    queryFn: () => fetchStock(page),
    placeholderData: (previous) => previous,
  })
}

export function useReceiveStock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ productId, quantity }: { productId: string; quantity: number }) =>
      receiveStock(productId, quantity),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: stockKeys.all }),
  })
}

export function useAdjustStock() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: { productId: string; quantityOnHand: number; reason: string }) =>
      adjustStock(input.productId, input.quantityOnHand, input.reason),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: stockKeys.all }),
  })
}
