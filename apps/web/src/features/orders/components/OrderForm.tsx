import { type FormEvent, useState } from 'react'

import type { OrderDraft } from '@/features/orders/types'
import { useProducts } from '@/features/products/hooks/useProducts'
import { useI18n } from '@/shared/i18n/useI18n'
import { Button } from '@/shared/ui/Button'
import { Field } from '@/shared/ui/Field'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

interface OrderFormProps {
  submitting: boolean
  error?: string | undefined
  onSubmit: (draft: OrderDraft) => void
  onCancel: () => void
}

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export function OrderForm({ submitting, error, onSubmit, onCancel }: OrderFormProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [quantities, setQuantities] = useState<Record<string, number>>({})
  const { t, format } = useI18n()
  const [errors, setErrors] = useState<{ name?: string; email?: string; items?: string }>({})

  // So produtos ativos podem ser vendidos - a mesma regra que o service aplica.
  const { data, isPending } = useProducts({ search: '', active: true, page: 1 })

  const selected = Object.entries(quantities).filter(([, quantity]) => quantity > 0)
  const total = (data?.items ?? []).reduce(
    (sum, product) => sum + (quantities[product.id] ?? 0) * product.priceInCents,
    0,
  )

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const nextErrors: typeof errors = {}
    if (!name.trim()) nextErrors.name = t.orders.customerRequired
    if (!EMAIL_PATTERN.test(email)) nextErrors.email = t.common.invalidEmail
    if (selected.length === 0) nextErrors.items = t.orders.itemsRequired

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    onSubmit({
      customer: { name: name.trim(), email: email.trim() },
      items: selected.map(([productId, quantity]) => ({ productId, quantity })),
    })
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      {error ? (
        <p className="form__error" role="alert">
          {error}
        </p>
      ) : null}

      <Field
        label={t.orders.customer}
        value={name}
        error={errors.name}
        onChange={(event) => setName(event.target.value)}
      />
      <Field
        label={t.common.email}
        type="email"
        value={email}
        error={errors.email}
        onChange={(event) => setEmail(event.target.value)}
      />

      <fieldset className="fieldset">
        <legend className="field__label">{t.orders.items}</legend>
        {errors.items ? (
          <p className="field__error" role="alert">
            {errors.items}
          </p>
        ) : null}

        {isPending ? <SkeletonRows rows={3} /> : null}

        {data?.items.length === 0 ? (
          <StateMessage
            kind="empty"
            title={t.orders.noActiveProducts}
            description={t.orders.noActiveProductsHint}
          />
        ) : null}

        <ul className="picker">
          {(data?.items ?? []).map((product) => (
            <li key={product.id} className="picker__row">
              <div>
                <span className="picker__name">{product.name}</span>
                <span className="picker__meta">
                  <code>{product.sku}</code> &middot; {format.currency(product.priceInCents)}
                </span>
              </div>
              <input
                type="number"
                min={0}
                className="field__input picker__quantity"
                aria-label={t.orders.quantityOf(product.name)}
                value={quantities[product.id] ?? 0}
                onChange={(event) =>
                  setQuantities((current) => ({
                    ...current,
                    [product.id]: Math.max(0, Number(event.target.value) || 0),
                  }))
                }
              />
            </li>
          ))}
        </ul>
      </fieldset>

      <p className="form__total">
        {t.common.total}: <strong>{format.currency(total)}</strong>
      </p>

      <div className="form__actions">
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t.common.cancel}
        </Button>
        <Button type="submit" loading={submitting}>
          {t.orders.createOrder}
        </Button>
      </div>
    </form>
  )
}
