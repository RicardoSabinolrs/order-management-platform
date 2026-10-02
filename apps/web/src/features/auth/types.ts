export interface Credentials {
  email: string
  password: string
}

export interface AuthenticatedUser {
  id: string
  name: string
  email: string
  role: 'admin' | 'operator' | 'viewer'
  avatarUrl: string | null
}

export interface LoginResult {
  accessToken: string
  user: AuthenticatedUser
}
