/**
 * Erros da API no formato RFC 9457 (`application/problem+json`).
 *
 * O backend responde sempre nesse formato, entao a tela trata falha de negocio
 * e falha de rede pelo mesmo caminho.
 */

export interface Problem {
  type: string
  title: string
  status: number
  detail: string
  code: string
  instance: string
  /** Campos extras que o backend anexa (ex.: `dependencies` no readiness). */
  [key: string]: unknown
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly problem: Problem

  constructor(problem: Problem) {
    super(problem.detail || problem.title)
    this.name = 'ApiError'
    this.status = problem.status
    this.code = problem.code
    this.problem = problem
  }

  get isUnauthorized(): boolean {
    return this.status === 401
  }
}

export function isProblem(payload: unknown): payload is Problem {
  return (
    typeof payload === 'object' &&
    payload !== null &&
    'code' in payload &&
    'status' in payload
  )
}
