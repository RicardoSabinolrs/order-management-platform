import { type FormEvent, useState } from 'react'

import type { ProductDraft } from '@/features/products/types'
import { useI18n } from '@/shared/i18n/useI18n'
import { Button } from '@/shared/ui/Button'
import { Field } from '@/shared/ui/Field'

interface ProductFormProps {
  submitting: boolean
  error?: string | undefined
  onSubmit: (draft: ProductDraft) => void
  onCancel: () => void
}

interface Errors {
  sku?: string
  name?: string
  price?: string
}

// Mesmo formato exigido pelo dominio no backend. Validar aqui evita uma ida ao
// servidor; a validacao que vale continua sendo a de la.
const SKU_PATTERN = /^[A-Z0-9][A-Z0-9-]{2,31}$/

export function ProductForm({ submitting, error, onSubmit, onCancel }: ProductFormProps) {
  const [sku, setSku] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [price, setPrice] = useState('')
  const [initialStock, setInitialStock] = useState('0')
  const [errors, setErrors] = useState<Errors>({})
  const { t } = useI18n()

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const nextErrors: Errors = {}
    const normalizedSku = sku.trim().toUpperCase()
    if (!SKU_PATTERN.test(normalizedSku)) {
      nextErrors.sku = t.products.skuInvalid
    }
    if (!name.trim()) nextErrors.name = t.products.nameRequired

    const priceValue = Number(price.replace(',', '.'))
    if (!Number.isFinite(priceValue) || priceValue < 0) {
      nextErrors.price = t.products.priceInvalid
    }

    setErrors(nextErrors)
    if (Object.keys(nextErrors).length > 0) return

    onSubmit({
      sku: normalizedSku,
      name: name.trim(),
      description: description.trim(),
      // A API trabalha em centavos: o arredondamento acontece na fronteira.
      priceInCents: Math.round(priceValue * 100),
      initialStock: Math.max(0, Number(initialStock) || 0),
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
        label="SKU"
        value={sku}
        error={errors.sku}
        hint={t.products.skuHint}
        onChange={(event) => setSku(event.target.value)}
      />
      <Field
        label={t.common.name}
        value={name}
        error={errors.name}
        onChange={(event) => setName(event.target.value)}
      />
      <Field
        label={t.products.description}
        value={description}
        onChange={(event) => setDescription(event.target.value)}
      />
      <Field
        label={t.products.price}
        inputMode="decimal"
        value={price}
        error={errors.price}
        placeholder={t.products.pricePlaceholder}
        onChange={(event) => setPrice(event.target.value)}
      />
      <Field
        label={t.products.initialStock}
        type="number"
        min={0}
        value={initialStock}
        onChange={(event) => setInitialStock(event.target.value)}
      />

      <div className="form__actions">
        <Button type="button" variant="secondary" onClick={onCancel}>
          {t.common.cancel}
        </Button>
        <Button type="submit" loading={submitting}>
          {t.products.register}
        </Button>
      </div>
    </form>
  )
}
