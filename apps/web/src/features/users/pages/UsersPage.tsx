import { useState } from 'react'

import { useAuth } from '@/features/auth/hooks/useAuth'
import { UserForm } from '@/features/users/components/UserForm'
import { useCreateUser, useUsers } from '@/features/users/hooks/useUsers'
import type { UserDraft } from '@/features/users/types'
import { ApiError } from '@/shared/api/problem'
import { useI18n } from '@/shared/i18n/useI18n'
import { useToast } from '@/shared/toast/useToast'
import { Avatar } from '@/shared/ui/Avatar'
import { Button } from '@/shared/ui/Button'
import { Card } from '@/shared/ui/Card'
import { IconPlus } from '@/shared/ui/icons'
import { Modal } from '@/shared/ui/Modal'
import { Pagination } from '@/shared/ui/Pagination'
import { SkeletonRows } from '@/shared/ui/Skeleton'
import { StateMessage } from '@/shared/ui/StateMessage'

export function UsersPage() {
  const { t } = useI18n()
  const { user: sessao } = useAuth()
  const { notify } = useToast()
  const [page, setPage] = useState(1)
  const [creating, setCreating] = useState(false)

  const { data, isPending, isError, error, isFetching } = useUsers(page)
  const createUser = useCreateUser()

  // 403 nao e falha: e a regra funcionando. Merece explicacao, nao alerta.
  const proibido = error instanceof ApiError && error.status === 403
  const podeCadastrar = sessao?.role === 'admin'

  function handleCreate(draft: UserDraft) {
    createUser.mutate(draft, {
      onSuccess: (created) => {
        setCreating(false)
        notify({ tone: 'success', title: t.users.created(created.name), detail: t.users.createdDetail })
      },
    })
  }

  return (
    <Card
      title={t.users.title}
      description={data ? t.users.count(data.total) : t.common.loading}
      padding="flush"
      actions={
        podeCadastrar ? (
          <Button
            icon={<IconPlus size={15} />}
            onClick={() => {
              createUser.reset()
              setCreating(true)
            }}
          >
            {t.users.newUser}
          </Button>
        ) : undefined
      }
    >
      {isPending && !proibido ? <SkeletonRows rows={4} /> : null}

      {proibido ? (
        <StateMessage kind="empty" title={t.users.forbiddenTitle} description={t.users.forbiddenHint} />
      ) : null}

      {isError && !proibido ? (
        <StateMessage kind="error" title={t.users.loadError} description={error.message} />
      ) : null}

      {data && data.items.length === 0 ? (
        <StateMessage kind="empty" title={t.users.empty} description={t.users.emptyHint} />
      ) : null}

      {data && data.items.length > 0 ? (
        <>
          <div className="table-wrapper" data-fetching={isFetching}>
            <table className="table">
              <caption className="visually-hidden">{t.users.caption}</caption>
              <thead>
                <tr>
                  <th scope="col">{t.users.colUser}</th>
                  <th scope="col">{t.common.email}</th>
                  <th scope="col">{t.users.colRole}</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((usuario) => (
                  <tr key={usuario.id}>
                    <td>
                      <span className="person">
                        <Avatar name={usuario.name} src={usuario.avatarUrl} size={36} />
                        <span className="table__primary">{usuario.name}</span>
                        {usuario.id === sessao?.id ? (
                          <span className="tag">{t.users.you}</span>
                        ) : null}
                      </span>
                    </td>
                    <td>{usuario.email}</td>
                    <td>
                      <span className="role-badge" data-role={usuario.role}>
                        {t.roles[usuario.role]}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pagination page={data.page} pages={data.pages} total={data.total} onChange={setPage} />
        </>
      ) : null}

      <Modal title={t.users.newUser} open={creating} onClose={() => setCreating(false)}>
        <UserForm
          submitting={createUser.isPending}
          error={createUser.error?.message}
          onSubmit={handleCreate}
          onCancel={() => setCreating(false)}
        />
      </Modal>
    </Card>
  )
}
