import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { OrderStatusBadge } from '@/features/orders/components/OrderStatusBadge'
import { useOrder, useOrderTransition } from '@/features/orders/hooks/useOrders'
import { ALLOWED_TRANSITIONS } from '@/features/orders/types'
import { useI18n } from '@/shared/i18n/useI18n'
import { useToast } from '@/shared/toast/useToast'
import { Button } from '@/shared/ui/Button'
import { Card } from '@/shared/ui/Card'
import { Field } from '@/shared/ui/Field'
import { IconAlert, IconChevronLeft } from '@/shared/ui/icons'
import { Modal } from '@/shared/ui/Modal'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

export function OrderDetailPage() {
  const { orderId = '' } = useParams<{ orderId: string }>()
  const { data: order, isPending, isError, error } = useOrder(orderId)
  const transition = useOrderTransition(orderId)
  const { notify } = useToast()
  const { t, format } = useI18n()

  const [cancelling, setCancelling] = useState(false)
  const [reason, setReason] = useState('')

  if (isPending) {
    return (
      <Card title={t.orders.loadingOne}>
        <SkeletonRows rows={5} />
      </Card>
    )
  }

  if (isError) {
    return (
      <StateMessage
        kind="error"
        title={t.orders.loadOneError}
        description={error.message}
        action={
          <Link className="btn btn--secondary" to="/pedidos">
            <IconChevronLeft size={14} />
            {t.orders.backToList}
          </Link>
        }
      />
    )
  }

  // A interface so oferece as transicoes que o dominio aceita: o botao para uma
  // acao impossivel nunca chega a aparecer.
  const nextStatuses = ALLOWED_TRANSITIONS[order.status]

  return (
    <div className="stack">
      <Card
        title={t.orders.title(order.reference)}
        description={t.orders.createdAt(format.dateTime(order.placedAt))}
        actions={
          <>
            <OrderStatusBadge status={order.status} />
            <Link className="btn btn--ghost btn--sm" to="/pedidos">
              <IconChevronLeft size={14} />
              {t.common.back}
            </Link>
          </>
        }
      >
        <dl className="definitions">
          <div>
            <dt>{t.orders.customer}</dt>
            <dd>{order.customer.name}</dd>
          </div>
          <div>
            <dt>{t.common.email}</dt>
            <dd>{order.customer.email}</dd>
          </div>
          <div>
            <dt>{t.orders.updatedAt}</dt>
            <dd>{format.dateTime(order.updatedAt)}</dd>
          </div>
          <div>
            <dt>{t.common.total}</dt>
            <dd className="definitions__emphasis">{format.currency(order.totalInCents)}</dd>
          </div>
        </dl>

        {order.cancellationReason ? (
          <p className="alert alert--error" style={{ marginTop: '1rem' }}>
            <IconAlert size={15} />
            {t.orders.cancelledBecause(order.cancellationReason)}
          </p>
        ) : null}
      </Card>

      <Card title={t.orders.items} padding="flush">
        <div className="table-wrapper">
          <table className="table">
            <thead>
              <tr>
                <th scope="col">{t.orders.colSku}</th>
                <th scope="col">{t.orders.colDescription}</th>
                <th scope="col" className="table__number">
                  {t.orders.colQuantity}
                </th>
                <th scope="col" className="table__number">
                  {t.orders.colUnitPrice}
                </th>
                <th scope="col" className="table__number">
                  {t.orders.colSubtotal}
                </th>
              </tr>
            </thead>
            <tbody>
              {order.items.map((item) => (
                <tr key={item.productId}>
                  <td>
                    <code>{item.sku}</code>
                  </td>
                  <td className="table__primary">{item.description}</td>
                  <td className="table__number">{item.quantity}</td>
                  <td className="table__number">{format.currency(item.unitPriceInCents)}</td>
                  <td className="table__number">{format.currency(item.subtotalInCents)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card
        title={t.orders.actionsTitle}
        description={
          nextStatuses.length === 0
            ? t.orders.endOfLifecycle
            : t.orders.transitionsHint
        }
      >
        {transition.isError ? (
          <p className="alert alert--error" role="alert" style={{ marginBottom: '1rem' }}>
            <IconAlert size={15} />
            {transition.error.message}
          </p>
        ) : null}

        {nextStatuses.length === 0 ? (
          <p className="field__hint">{t.orders.noActions}</p>
        ) : (
          <div className="card__actions">
            {nextStatuses.map((target) =>
              target === 'cancelled' ? (
                <Button key={target} variant="danger" onClick={() => setCancelling(true)}>
                  {t.orders.cancelOrder}
                </Button>
              ) : (
                <Button
                  key={target}
                  disabled={transition.isPending}
                  onClick={() =>
                    transition.mutate(target as 'confirmed' | 'shipped' | 'delivered', {
                      onSuccess: (updated) =>
                        notify({
                          tone: 'success',
                          title: t.orders.transitioned(updated.reference, t.status[updated.status]),
                          detail:
                            updated.status === 'shipped'
                              ? t.orders.stockWrittenOff
                              : undefined,
                        }),
                    })
                  }
                >
                  {t.status[target]}
                </Button>
              ),
            )}
          </div>
        )}
      </Card>

      <Modal title={t.orders.cancelOrder} open={cancelling} onClose={() => setCancelling(false)}>
        <div className="form">
          <Field
            label={t.orders.reason}
            value={reason}
            hint={t.orders.reasonHint}
            onChange={(event) => setReason(event.target.value)}
          />
          <div className="form__actions">
            <Button variant="secondary" onClick={() => setCancelling(false)}>
              {t.common.back}
            </Button>
            <Button
              variant="danger"
              loading={transition.isPending}
              disabled={reason.trim().length < 3}
              onClick={() =>
                transition.mutate(
                  { cancel: reason.trim() },
                  {
                    onSuccess: (updated) => {
                      setCancelling(false)
                      notify({
                        tone: 'success',
                        title: t.orders.cancelled(updated.reference),
                        detail: t.orders.cancelledDetail,
                      })
                    },
                  },
                )
              }
            >
              {t.orders.confirmCancel}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
