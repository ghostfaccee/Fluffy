import { api } from '@/api/client'

function postPath(id) {
  if (!id) throw new TypeError('Не указан ID публикации')
  return `/posts/${encodeURIComponent(id)}`
}

function payload(data) {
  const title = String(data.title ?? '').trim()
  const content = String(data.content ?? '').trim()

  if (!title || title.length > 200) {
    throw new Error('Заголовок должен содержать от 1 до 200 символов')
  }

  if (!content || content.length > 4096) {
    throw new Error('Текст должен содержать от 1 до 4096 символов')
  }

  return { title, content }
}

export const postsApi = Object.freeze({
    listByUser(username, { limit = 20, offset = 0 } = {}) {
    const name = String(username ?? '').trim()

    if (!name) {
      throw new TypeError('Не указан username пользователя')
    }

    if (!Number.isInteger(limit) || limit < 1) {
      throw new TypeError('limit должен быть положительным целым числом')
    }

    if (!Number.isInteger(offset) || offset < 0) {
      throw new TypeError('offset должен быть неотрицательным целым числом')
    }

    const query = new URLSearchParams({
      limit: String(limit),
      offset: String(offset),
    })

    return api(`/users/${encodeURIComponent(name)}/posts?${query}`)
  },

  create(data) {
    return api('/posts', {
      method: 'POST',
      body: payload(data),
    })
  },

  get(id) {
    return api(postPath(id))
  },

  update(id, data) {
    return api(postPath(id), {
      method: 'PATCH',
      body: payload(data),
    })
  },

  remove(id) {
    return api(postPath(id), {
      method: 'DELETE',
    })
  },
})
