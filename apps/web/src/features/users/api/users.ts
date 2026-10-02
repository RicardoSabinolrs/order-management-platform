import type { User, UserDraft } from '@/features/users/types'
import { api } from '@/shared/api/client'
import { toPage, type Page } from '@/shared/api/page'
import type { PageDTO, UserDTO } from '@/shared/api/types'

export function toUser(dto: UserDTO): User {
  return {
    id: dto.id,
    name: dto.name,
    email: dto.email,
    role: dto.role,
    avatarUrl: dto.avatar_url,
  }
}

export async function fetchUsers(page: number): Promise<Page<User>> {
  const params = new URLSearchParams({ page: String(page), page_size: '10' })
  return toPage(await api.get<PageDTO<UserDTO>>(`/api/v1/users?${params.toString()}`), toUser)
}

export async function createUser(draft: UserDraft): Promise<User> {
  const dto = await api.post<UserDTO>('/api/v1/users', {
    name: draft.name,
    email: draft.email,
    password: draft.password,
    role: draft.role,
  })
  return toUser(dto)
}
