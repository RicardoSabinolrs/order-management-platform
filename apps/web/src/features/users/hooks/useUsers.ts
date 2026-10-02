import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { createUser, fetchUsers } from '@/features/users/api/users'
import type { UserDraft } from '@/features/users/types'

export const userKeys = {
  all: ['users'] as const,
  list: (page: number) => [...userKeys.all, 'list', page] as const,
}

export function useUsers(page: number) {
  return useQuery({
    queryKey: userKeys.list(page),
    queryFn: () => fetchUsers(page),
    placeholderData: (previous) => previous,
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (draft: UserDraft) => createUser(draft),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: userKeys.all }),
  })
}
