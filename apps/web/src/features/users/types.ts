export const USER_ROLES = ['admin', 'operator', 'viewer'] as const

export type UserRole = (typeof USER_ROLES)[number]

export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  avatarUrl: string | null
}

export interface UserDraft {
  name: string
  email: string
  password: string
  role: UserRole
}
