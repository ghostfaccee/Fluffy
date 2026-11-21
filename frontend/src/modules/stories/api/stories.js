import { api } from '@/shared/api/client'

export const STORY_LIMIT = 5
export const STORY_TITLE_LIMIT = 20

export const STORY_ACCEPT = [
  'image/jpeg',
  'image/png',
  'video/mp4',
  'video/mpeg',
].join(',')

const ALLOWED_CONTENT_TYPES = new Set(STORY_ACCEPT.split(','))

export function getStoryContentType(file) {
  const contentType = String(file?.type || '').toLowerCase()

  return ALLOWED_CONTENT_TYPES.has(contentType) ? contentType : null
}

export function isVideoStory(story) {
  try {
    const url = new URL(story.media_url, window.location.origin)

    return /\.(mp4|mpeg|mpg)$/i.test(url.pathname)
  } catch {
    return false
  }
}

export function isStoryActive(story, now = Date.now()) {
  const expiresAt = Date.parse(story.expires_at)

  return Number.isFinite(expiresAt) && expiresAt > now
}

export function sortStories(stories) {
  return [...stories].sort(
    (first, second) =>
      Date.parse(first.created_at) - Date.parse(second.created_at),
  )
}

export function storyErrorMessage(cause) {
  if (cause?.name === 'AbortError') {
    return 'Загрузка отменена.'
  }

  if (cause?.status === 0 || cause instanceof TypeError) {
    return 'Нет связи с сервером. Проверьте подключение и попробуйте снова.'
  }

  if (cause?.status === 401) {
    return 'Сессия истекла. Войдите в аккаунт снова.'
  }

  if (cause?.status === 403) {
    return 'Нет доступа к этой истории.'
  }

  if (cause?.status === 404) {
    return 'История не найдена или срок её действия закончился.'
  }

  if (cause?.status === 429) {
    return 'Слишком много запросов. Попробуйте немного позже.'
  }

  if (cause?.status === 422) {
    return 'Проверьте заголовок и формат файла.'
  }

  const detail = cause?.detail

  if (typeof detail === 'string' && detail.trim()) {
    return detail
  }

  if (cause instanceof Error && !cause?.status) {
    return cause.message
  }

  return 'Не удалось выполнить действие. Попробуйте позже.'
}

export function getUserStories(username) {
  return api(`/users/${encodeURIComponent(username)}/stories`)
}

export function getStoryArchive() {
  return api('/stories/archive')
}

export function getStory(storyId, { archive = false } = {}) {
  const id = encodeURIComponent(storyId)

  return api(archive ? `/stories/archive/${id}` : `/stories/${id}`)
}

export function deleteStory(storyId) {
  return api(`/stories/${encodeURIComponent(storyId)}`, {
    method: 'DELETE',
  })
}

export function createStory({ title, mediaKey }) {
  return api('/stories', {
    method: 'POST',
    body: {
      title,
      media_key: mediaKey,
    },
  })
}

export async function uploadStoryMedia(
  file,
  { signal, isCurrent = () => true } = {},
) {
  const contentType = getStoryContentType(file)

  if (!contentType) {
    throw new Error('Выберите JPEG, PNG, MP4 или MPEG.')
  }

  if (file.size === 0) {
    throw new Error('Выбранный файл пуст.')
  }

  const { upload_url: uploadUrl, key } = await api('/stories/upload-url', {
    method: 'POST',
    body: {
      content_type: contentType,
    },
  })

  if (signal?.aborted || !isCurrent()) {
    throw new DOMException('Upload aborted', 'AbortError')
  }

  // Запрос идёт непосредственно в S3.
  // Токены приложения и cookies сюда не передаются.
  const response = await fetch(uploadUrl, {
    method: 'PUT',
    headers: {
      'Content-Type': contentType,
    },
    body: file,
    credentials: 'omit',
    signal,
  })

  if (!response.ok) {
    throw new Error(
      'Не удалось загрузить файл в хранилище. Проверьте подключение и настройки CORS S3.',
    )
  }

  if (signal?.aborted || !isCurrent()) {
    throw new DOMException('Upload aborted', 'AbortError')
  }

  return key
}
