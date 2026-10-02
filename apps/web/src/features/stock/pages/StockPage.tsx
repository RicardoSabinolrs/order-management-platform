import { useState } from 'react'

import { useAdjustStock, useReceiveStock, useStock } from '@/features/stock/hooks/useStock'
import type { StockBalance } from '@/features/stock/types'
import { useI18n } from '@/shared/i18n/useI18n'
import { useToast } from '@/shared/toast/useToast'
import { Button } from '@/shared/ui/Button'
import { Card } from '@/shared/ui/Card'
import { Field } from '@/shared/ui/Field'
import { IconAlert } from '@/shared/ui/icons'
import { Modal } from '@/shared/ui/Modal'
import { Pagination } from '@/shared/ui/Pagination'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

type Dialog = { kind: 'receive' | 'adjust'; balance: StockBalance } | null

export function StockPage() {
  const [page, setPage] = useState(1)
  const [dialog, setDialog] = useState<Dialog>(null)
  const [quantity, setQuantity] = useState('')
  const [reason, setReason] = useState('')

  const { data, isPending, isError, error, isFetching } = useStock(page)
  const receive = useReceiveStock()
  const adjust = useAdjustStock()
  const { notify } = useToast()
  const { t, format } = useI18n()

  const mutationError = receive.error ?? adjust.error

  function open(kind: 'receive' | 'adjust', balance: StockBalance) {
    setDialog({ kind, balance })
    setQuantity(kind === 'adjust' ? String(balance.quantityOnHand) : '')
    setReason('')
    receive.reset()
    adjust.reset()
  }

  function submit() {
    if (!dialog) return
    const amount = Number(quantity)
    if (!Number.isFinite(amount)) return

    const onSuccess = (saldo: StockBalance) => {
      setDialog(null)
      notify({
        tone: 'success',
        title: t.stock.updated(saldo.sku),
        detail: t.stock.updatedDetail(saldo.quantityAvailable, saldo.quantityOnHand),
      })
    }

    if (dialog.kind === 'receive') {
      receive.mutate({ productId: dialog.balance.productId, quantity: amount }, { onSuccess })
    } else {
      adjust.mutate(
        { productId: dialog.balance.productId, quantityOnHand: amount, reason },
        { onSuccess },
      )
    }
  }

  return (
    <Card
      title={t.pages.stock.title}
      description={t.stock.description}
      padding="flush"
    >
      {isPending ? <SkeletonRows rows={6} /> : null}

      {isError ? (
        <StateMessage
          kind="error"
          title={t.stock.loadError}
          description={error.message}
        />
      ) : null}

      {data && data.items.length === 0 ? (
        <StateMessage
          kind="empty"
          title={t.stock.empty}
          description={t.stock.emptyHint}
        />
      ) : null}

      {data && data.items.length > 0 ? (
        <>
          <div className="table-wrapper" data-fetching={isFetching}>
            <table className="table">
              <caption className="visually-hidden">{t.stock.caption}</caption>
              <thead>
                <tr>
                  <th scope="col">{t.orders.colSku}</th>
                  <th scope="col" className="table__number">
                    {t.stock.colOnHand}
                  </th>
                  <th scope="col" className="table__number">
                    {t.stock.colReserved}
                  </th>
                  <th scope="col" className="table__number">
                    {t.stock.colAvailable}
                  </th>
                  <th scope="col">{t.stock.colUpdated}</th>
                  <th scope="col">
                    <span className="visually-hidden">{t.common.actions}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((balance) => (
                  <tr key={balance.productId}>
                    <td>
                      <code>{balance.sku}</code>
                    </td>
                    <td className="table__number">{balance.quantityOnHand}</td>
                    <td className="table__number">{balance.quantityReserved}</td>
                    <td className="table__number">
                      {balance.quantityAvailable === 0 ? (
                        <span className="badge" data-status="cancelled">
                          {t.stock.soldOut}
                        </span>
                      ) : (
                        <strong>{balance.quantityAvailable}</strong>
                      )}
                    </td>
                    <td>{format.dateTime(balance.updatedAt)}</td>
                    <td>
                      <div className="table__actions">
                        <Button variant="secondary" size="sm" onClick={() => open('receive', balance)}>
                          {t.stock.receive}
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => open('adjust', balance)}>
                          {t.stock.adjust}
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
        </>
      ) : null}

      <Modal
        title={
          dialog?.kind === 'adjust'
            ? t.stock.adjustTitle(dialog.balance.sku)
            : t.stock.receiveTitle(dialog?.balance.sku ?? '')
        }
        open={dialog !== null}
        onClose={() => setDialog(null)}
      >
        <div className="form">
          {mutationError ? (
            <p className="alert alert--error" role="alert">
              <IconAlert size={15} />
              {mutationError.message}
            </p>
          ) : null}

          <Field
            label={dialog?.kind === 'adjust' ? t.stock.countedBalance : t.stock.receivedQuantity}
            type="number"
            min={dialog?.kind === 'adjust' ? 0 : 1}
            value={quantity}
            hint={
              dialog?.kind === 'adjust'
                ? t.stock.cannotGoBelow(dialog.balance.quantityReserved)
                : undefined
            }
            onChange={(event) => setQuantity(event.target.value)}
          />

          {dialog?.kind === 'adjust' ? (
            <Field
              label={t.stock.reason}
              value={reason}
              hint={t.stock.reasonHint}
              onChange={(event) => setReason(event.target.value)}
            />
          ) : null}

          <div className="form__actions">
            <Button variant="secondary" onClick={() => setDialog(null)}>
              {t.common.cancel}
            </Button>
            <Button loading={receive.isPending || adjust.isPending} onClick={submit}>
              {t.common.confirm}
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  )
}
