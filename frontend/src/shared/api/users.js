import { api } from '@/shared/api/client'

export function fetchUserById(userId) {
  return api(`/users/id/${encodeURIComponent(userId)}`)
}
