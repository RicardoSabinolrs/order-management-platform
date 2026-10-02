import { useMemo, useState } from 'react'

import { ProductForm } from '@/features/products/components/ProductForm'
import {
  useCreateProduct,
  useDeleteProduct,
  useProducts,
  useUpdateProduct,
} from '@/features/products/hooks/useProducts'
import type { Product, ProductDraft } from '@/features/products/types'
import { useI18n } from '@/shared/i18n/useI18n'
import { useToast } from '@/shared/toast/useToast'
import { Button } from '@/shared/ui/Button'
import { Card } from '@/shared/ui/Card'
import { IconPlus, IconSearch } from '@/shared/ui/icons'
import { Modal } from '@/shared/ui/Modal'
import { Pagination } from '@/shared/ui/Pagination'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

export function ProductsPage() {
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [creating, setCreating] = useState(false)

  const filters = useMemo(() => ({ search, active: null, page }), [search, page])
  const { data, isPending, isError, error, isFetching } = useProducts(filters)

  const createProduct = useCreateProduct()
  const updateProduct = useUpdateProduct()
  const deleteProduct = useDeleteProduct()
  const { notify } = useToast()
  const { t, format } = useI18n()

  function handleCreate(draft: ProductDraft) {
    createProduct.mutate(draft, {
      onSuccess: (product) => {
        setCreating(false)
        notify({
          tone: 'success',
          title: t.products.created(product.sku),
          detail: t.products.createdDetail,
        })
      },
    })
  }

  function toggleActive(product: Product) {
    updateProduct.mutate(
      { productId: product.id, patch: { active: !product.active } },
      {
        onSuccess: (updated) =>
          notify({
            tone: 'success',
            title: updated.active ? t.products.reactivated(updated.sku) : t.products.deactivated(updated.sku),
          }),
        onError: (mutationError) =>
          notify({ tone: 'error', title: t.products.changeFailed, detail: mutationError.message }),
      },
    )
  }

  function remove(product: Product) {
    deleteProduct.mutate(product.id, {
      onSuccess: () => notify({ tone: 'success', title: t.products.deleted(product.sku) }),
      onError: (mutationError) =>
        notify({ tone: 'error', title: t.products.deleteRefused, detail: mutationError.message }),
    })
  }

  return (
    <Card
      title={t.pages.products.title}
      description={data ? t.products.count(data.total) : t.common.loading}
      padding="flush"
      actions={
        <Button icon={<IconPlus size={15} />} onClick={() => setCreating(true)}>
          {t.products.newProduct}
        </Button>
      }
    >
      <div className="toolbar">
        <label className="toolbar__search">
          <span className="visually-hidden">{t.products.searchPlaceholder}</span>
          <IconSearch size={15} />
          <input
            type="search"
            className="input"
            placeholder={t.products.searchPlaceholder}
            value={search}
            onChange={(event) => {
              setSearch(event.target.value)
              setPage(1)
            }}
          />
        </label>
      </div>

      {isPending ? <SkeletonRows rows={6} /> : null}

      {isError ? (
        <StateMessage
          kind="error"
          title={t.products.loadError}
          description={error.message}
        />
      ) : null}

      {data && data.items.length === 0 ? (
        <StateMessage
          kind="empty"
          title={t.products.empty}
          description={t.products.emptyHint}
        />
      ) : null}

      {data && data.items.length > 0 ? (
        <>
          <div className="table-wrapper" data-fetching={isFetching}>
            <table className="table">
              <caption className="visually-hidden">{t.products.caption}</caption>
              <thead>
                <tr>
                  <th scope="col">SKU</th>
                  <th scope="col">{t.products.colProduct}</th>
                  <th scope="col" className="table__number">
                    {t.products.colPrice}
                  </th>
                  <th scope="col">{t.products.colSituation}</th>
                  <th scope="col">
                    <span className="visually-hidden">{t.common.actions}</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((product) => (
                  <tr key={product.id}>
                    <td>
                      <code>{product.sku}</code>
                    </td>
                    <td>
                      <span className="table__primary">{product.name}</span>
                      {product.description ? (
                        <span className="table__meta">{product.description}</span>
                      ) : null}
                    </td>
                    <td className="table__number">{format.currency(product.priceInCents)}</td>
                    <td>
                      <span className="badge" data-tone={product.active ? 'on' : 'off'}>
                        {product.active ? t.products.active : t.products.inactive}
                      </span>
                    </td>
                    <td>
                      <div className="table__actions">
                        <Button
                          variant="secondary"
                          size="sm"
                          disabled={updateProduct.isPending}
                          onClick={() => toggleActive(product)}
                        >
                          {product.active ? t.products.deactivate : t.products.activate}
                        </Button>
                        <Button
                          variant="danger"
                          size="sm"
                          disabled={deleteProduct.isPending}
                          onClick={() => remove(product)}
                        >
                          {t.products.delete}
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

      <Modal title={t.products.newProduct} open={creating} onClose={() => setCreating(false)}>
        <ProductForm
          submitting={createProduct.isPending}
          error={createProduct.error?.message}
          onSubmit={handleCreate}
          onCancel={() => setCreating(false)}
        />
      </Modal>
    </Card>
  )
}
