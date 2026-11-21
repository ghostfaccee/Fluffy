import { api } from '@/shared/api/client'

export const POST_MEDIA_ACCEPT = 'image/jpeg,image/png,video/mp4,video/mpeg'

const allowedMediaTypes = new Set(POST_MEDIA_ACCEPT.split(','))

export function getPostMediaType(file) {
  const type = String(file?.type ?? '').toLowerCase()
  return allowedMediaTypes.has(type) ? type : null
}

export function validatePostMedia(file) {
  const type = getPostMediaType(file)

  if (!type) throw new Error('Выберите JPEG, PNG, MP4 или MPEG.')
  if (file.size === 0) throw new Error('Выбранный файл пуст.')

  return type
}

export function isPostVideo(url) {
  if (!url) return false

  try {
    const { pathname } = new URL(url, window.location.origin)
    return /\.(mp4|mpeg|mpg)$/i.test(pathname)
  } catch {
    return false
  }
}

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

  const body = { title, content }

  // При редактировании текста не трогаем существующее вложение.
  if (data.mediaKey !== undefined) {
    body.media_key = data.mediaKey
  }

  return body
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

  async uploadMedia(file, { signal } = {}) {
    const contentType = validatePostMedia(file)

    signal?.throwIfAborted()

    const { upload_url: uploadUrl, key } = await api('/posts/upload-url', {
      method: 'POST',
      body: { content_type: contentType },
    })

    signal?.throwIfAborted()

    if (!uploadUrl || !key) {
      throw new Error('Сервер не вернул ссылку для загрузки вложения.')
    }

    let response

    try {
      // В S3 отправляем сам файл, без FormData, токенов и cookies.
      response = await fetch(uploadUrl, {
        method: 'PUT',
        headers: { 'Content-Type': contentType },
        body: file,
        credentials: 'omit',
        signal,
      })
    } catch (cause) {
      if (signal?.aborted) throw cause
      throw new Error('Не удалось связаться с хранилищем. Проверьте подключение.')
    }

    if (!response.ok) {
      throw new Error(`Хранилище не приняло файл (HTTP ${response.status}).`)
    }

    signal?.throwIfAborted()

    return key
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
