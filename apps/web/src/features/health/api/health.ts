import { api } from '@/shared/api/client'
import { ApiError } from '@/shared/api/problem'

export interface DependencyStatus {
  name: string
  healthy: boolean
}

export interface Readiness {
  status: 'ready' | 'degraded'
  dependencies: DependencyStatus[]
}

/**
 * O readiness responde 503 quando degradado, e o backend anexa o estado de
 * cada dependencia no corpo `problem+json`. Para esta tela isso e informacao
 * valida, nao erro: o objetivo e justamente mostrar o que caiu.
 */
export async function fetchReadiness(): Promise<Readiness> {
  try {
    return await api.get<Readiness>('/health/ready', { anonymous: true })
  } catch (error) {
    if (error instanceof ApiError && error.status === 503) {
      const dependencies = error.problem.dependencies
      return {
        status: 'degraded',
        dependencies: Array.isArray(dependencies) ? (dependencies as DependencyStatus[]) : [],
      }
    }
    throw error
  }
}
