import { api } from '@/shared/api/client'

function friendshipPath(userId) {
  return `/friendships/${encodeURIComponent(userId)}`
}

export const friendshipsApi = Object.freeze({
  list(kind, profileUserId) {
    const path = `/friendships/all/${kind}`
    return api(profileUserId ? `${path}/${encodeURIComponent(profileUserId)}` : path)
  },

  async get(userId) {
    try {
      return await api(friendshipPath(userId))
    } catch (error) {
      if (error?.status === 404 && error.detail === 'Friendship does not exists') {
        return null
      }
      throw error
    }
  },

  create(userId) {
    return api(friendshipPath(userId), { method: 'POST' })
  },

  accept(userId) {
    return api(`/friendships/accept/${encodeURIComponent(userId)}`, { method: 'PATCH' })
  },

  remove(userId) {
    return api(friendshipPath(userId), { method: 'DELETE' })
  },
})

export function friendshipErrorMessage(error, fallback) {
  if (error?.status === 0) return 'Нет связи с сервером.'
  if (error?.status === 429) return 'Слишком много запросов. Попробуйте позже.'
  return fallback
}
