import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import {
  cancelOrder,
  confirmOrder,
  createOrder,
  deliverOrder,
  fetchOrder,
  fetchOrders,
  shipOrder,
} from '@/features/orders/api/orders'
import type { OrderDraft, OrderFilters, OrderStatus } from '@/features/orders/types'

export const orderKeys = {
  all: ['orders'] as const,
  list: (filters: OrderFilters) => [...orderKeys.all, 'list', filters] as const,
  detail: (orderId: string) => [...orderKeys.all, 'detail', orderId] as const,
}

export function useOrders(filters: OrderFilters) {
  return useQuery({
    queryKey: orderKeys.list(filters),
    queryFn: () => fetchOrders(filters),
    placeholderData: (previous) => previous,
  })
}

export function useOrder(orderId: string) {
  return useQuery({
    queryKey: orderKeys.detail(orderId),
    queryFn: () => fetchOrder(orderId),
    enabled: orderId !== '',
  })
}

export function useCreateOrder() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (draft: OrderDraft) => createOrder(draft),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: orderKeys.all })
      // Criar pedido reserva estoque: os saldos mudaram.
      void queryClient.invalidateQueries({ queryKey: ['stock'] })
    },
  })
}

const TRANSITIONS = {
  confirmed: confirmOrder,
  shipped: shipOrder,
  delivered: deliverOrder,
} as const

type TransitionTarget = keyof typeof TRANSITIONS

export function useOrderTransition(orderId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (target: TransitionTarget | { cancel: string }) =>
      typeof target === 'string'
        ? TRANSITIONS[target](orderId)
        : cancelOrder(orderId, target.cancel),
    onSuccess: (order) => {
      queryClient.setQueryData(orderKeys.detail(orderId), order)
      void queryClient.invalidateQueries({ queryKey: orderKeys.all })
      // Envio baixa e cancelamento libera: em ambos os casos o saldo mudou.
      void queryClient.invalidateQueries({ queryKey: ['stock'] })
    },
  })
}

export type { OrderStatus, TransitionTarget }
