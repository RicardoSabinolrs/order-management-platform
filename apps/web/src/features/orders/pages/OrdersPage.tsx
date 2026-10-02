import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'

import { OrderFiltersBar } from '@/features/orders/components/OrderFiltersBar'
import { OrderForm } from '@/features/orders/components/OrderForm'
import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import { useCreateOrder, useOrders } from '@/features/orders/hooks/useOrders'
import type { OrderDraft, OrderStatus } from '@/features/orders/types'
import { useI18n } from '@/shared/i18n/useI18n'
import { useToast } from '@/shared/toast/useToast'
import { Button } from '@/shared/ui/Button'
import { Card } from '@/shared/ui/Card'
import { IconPlus } from '@/shared/ui/icons'
import { Modal } from '@/shared/ui/Modal'
import { Pagination } from '@/shared/ui/Pagination'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

export function OrdersPage() {
  const [status, setStatus] = useState<OrderStatus | 'all'>('all')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [creating, setCreating] = useState(false)

  const filters = useMemo(() => ({ status, search, page }), [status, search, page])
  const { data, isPending, isError, error, isFetching } = useOrders(filters)
  const createOrder = useCreateOrder()
  const { notify } = useToast()
  const { t, format } = useI18n()

  function handleCreate(draft: OrderDraft) {
    createOrder.mutate(draft, {
      onSuccess: (order) => {
        setCreating(false)
        notify({
          tone: 'success',
          title: t.orders.created(order.reference),
          detail: t.orders.createdDetail,
        })
      },
    })
  }

  return (
    <Card
      title={t.pages.orders.title}
      description={data ? t.orders.count(data.total) : t.common.loading}
      padding="flush"
      actions={
        <Button icon={<IconPlus size={15} />} onClick={() => setCreating(true)}>
          {t.orders.newOrder}
        </Button>
      }
    >
      <OrderFiltersBar
        status={status}
        search={search}
        onStatusChange={(next) => {
          setStatus(next)
          setPage(1) // Trocar o filtro sem voltar a pagina 1 mostra tela vazia.
        }}
        onSearchChange={(next) => {
          setSearch(next)
          setPage(1)
        }}
      />

      {isPending ? <SkeletonRows rows={6} /> : null}

      {isError ? (
        <StateMessage
          kind="error"
          title={t.orders.loadError}
          description={error.message}
        />
      ) : null}

      {data && data.items.length === 0 ? (
        <StateMessage
          kind="empty"
          title={t.orders.empty}
          description={t.orders.emptyHint}
        />
      ) : null}

      {data && data.items.length > 0 ? (
        <>
          <div className="table-wrapper" data-fetching={isFetching}>
            <table className="table">
              <caption className="visually-hidden">{t.orders.listCaption}</caption>
              <thead>
                <tr>
                  <th scope="col">{t.dashboard.colReference}</th>
                  <th scope="col">{t.dashboard.colCustomer}</th>
                  <th scope="col">{t.dashboard.colStatus}</th>
                  <th scope="col" className="table__number">
                    {t.dashboard.colItems}
                  </th>
                  <th scope="col" className="table__number">
                    {t.dashboard.colTotal}
                  </th>
                  <th scope="col">{t.dashboard.colCreatedAt}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((order) => (
                  <tr key={order.id}>
                    <td>
                      <Link className="table__link" to={`/pedidos/${order.id}`}>
                        {order.reference}
                      </Link>
                    </td>
                    <td className="table__primary">{order.customerName}</td>
                    <td>
                      <OrderStatusBadge status={order.status} />
                    </td>
                    <td className="table__number">{order.itemCount}</td>
                    <td className="table__number">{format.currency(order.totalInCents)}</td>
                    <td>{format.dateTime(order.placedAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination
            page={data.page}
            pages={data.pages}
            total={data.total}
            onChange={setPage}
          />
        </>
      ) : null}

      <Modal title={t.orders.newOrder} open={creating} onClose={() => setCreating(false)}>
        <OrderForm
          submitting={createOrder.isPending}
          error={createOrder.error?.message}
          onSubmit={handleCreate}
          onCancel={() => setCreating(false)}
        />
      </Modal>
    </Card>
  )
}
