import type { AuthenticatedUser, Credentials, LoginResult } from '@/features/auth/types'
import { api } from '@/shared/api/client'
import type { LoginResponseDTO, UserDTO } from '@/shared/api/types'

function toUser(dto: UserDTO): AuthenticatedUser {
  return { id: dto.id, name: dto.name, email: dto.email, role: dto.role, avatarUrl: dto.avatar_url }
}

export async function login(credentials: Credentials): Promise<LoginResult> {
  // `anonymous`: a rota de login nao deve mandar um token antigo junto.
  const dto = await api.post<LoginResponseDTO>('/api/v1/auth/login', credentials, {
    anonymous: true,
  })
  return { accessToken: dto.access_token, user: toUser(dto.user) }
}

export async function fetchCurrentUser(): Promise<AuthenticatedUser> {
  return toUser(await api.get<UserDTO>('/api/v1/auth/me'))
}
