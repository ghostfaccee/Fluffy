import { computed, ref } from 'vue'
import { api } from '@/shared/api/client'
import { useAuthStore } from '@/modules/auth/stores/auth'

function normalizeContentType(file) {
  const type = (file.type || '').toLowerCase().split(';')[0].trim()

  if (['audio/mpeg', 'audio/mp3', 'audio/x-mp3'].includes(type)) {
    return 'audio/mpeg'
  }

  if (
    ['audio/wav', 'audio/wave', 'audio/x-wav', 'audio/vnd.wave'].includes(type)
  ) {
    return 'audio/wav'
  }

  // Некоторые браузеры не определяют MIME-тип локальных аудиофайлов.
  // Расширение используем только при отсутствии конкретного MIME-типа.
  if (!type || type === 'application/octet-stream') {
    const extension = file.name.split('.').pop()?.toLowerCase()

    if (extension === 'mp3') return 'audio/mpeg'
    if (extension === 'wav') return 'audio/wav'
  }

  return null
}

function operationError(cause, stage) {
  if (cause?.status === 429) {
    return 'Слишком много запросов. Попробуйте позже.'
  }

  if (cause?.status === 401) {
    return 'Сессия истекла. Войдите в аккаунт повторно.'
  }

  if (cause?.status === 403) {
    return 'Недостаточно прав для изменения музыки.'
  }

  if (cause?.status === 0) {
    return 'Нет связи с сервером. Проверьте подключение и попробуйте снова.'
  }

  if (cause?.status === 413) {
    return 'Файл слишком большой для загрузки.'
  }

  if (cause?.status === 422) {
    return 'Сервер отклонил данные. Выберите файл MP3 или WAV и попробуйте снова.'
  }

  if (stage === 'storage') {
    return 'Не удалось загрузить музыку в хранилище. Проверьте подключение и попробуйте снова.'
  }

  if (stage === 'save') {
    return 'Не удалось сохранить музыку в профиле. Обновите страницу, чтобы проверить состояние профиля.'
  }

  if (stage === 'delete') {
    return 'Не удалось удалить музыку. Обновите страницу, чтобы проверить состояние профиля.'
  }

  return 'Не удалось подготовить загрузку музыки. Попробуйте снова.'
}

export function useMusicUpload() {
  const auth = useAuthStore()

  const operation = ref('')
  const error = ref('')

  const uploading = computed(() => operation.value === 'upload')
  const removing = computed(() => operation.value === 'delete')
  const busy = computed(() => operation.value !== '')

  function isCurrentUser(userId) {
    return (
      auth.user?.user_id != null &&
      String(auth.user.user_id) === String(userId)
    )
  }

  function updateMusicUrl(userId, musicUrl) {
    if (!isCurrentUser(userId)) return

    // Меняем только музыку, чтобы не перезаписать свежие изменения
    // аватара или других полей профиля параллельным ответом.
    auth.setUser({
      ...auth.user,
      music_url: musicUrl,
    })
  }

  async function upload(file) {
    if (busy.value) return false

    error.value = ''

    if (!file) return false

    const userId = auth.user?.user_id

    if (userId == null) {
      error.value = 'Войдите в аккаунт, чтобы добавить музыку.'
      return false
    }

    const contentType = normalizeContentType(file)

    if (!contentType) {
      error.value = 'Можно загрузить только MP3 или WAV.'
      return false
    }

    if (file.size === 0) {
      error.value = 'Выбранный файл пустой.'
      return false
    }

    operation.value = 'upload'
    let stage = 'prepare'

    try {
      const { upload_url, key } = await api('/users/me/music/upload-url', {
        method: 'POST',
        body: { content_type: contentType },
      })

      if (
        typeof upload_url !== 'string' ||
        !upload_url ||
        typeof key !== 'string' ||
        !key
      ) {
        throw new Error('Invalid music upload response')
      }

      if (!isCurrentUser(userId)) return false

      stage = 'storage'

      // Presigned URL уже содержит разрешение на загрузку.
      // API-клиент здесь не используем: токен приложения S3 не нужен.
      const response = await fetch(upload_url, {
        method: 'PUT',
        headers: {
          'Content-Type': contentType,
        },
        credentials: 'omit',
        body: file,
      })

      if (!response.ok) {
        throw new Error(`Music upload failed: ${response.status}`)
      }

      if (!isCurrentUser(userId)) return false

      stage = 'save'

      // Старый трек заранее не удаляем:
      // заменой и удалением старого объекта занимается бэкенд.
      const user = await api('/users/me/music', {
        method: 'PUT',
        body: { key },
      })

      updateMusicUrl(userId, user.music_url ?? null)

      return true
    } catch (cause) {
      if (isCurrentUser(userId)) {
        error.value = operationError(cause, stage)
      }

      return false
    } finally {
      operation.value = ''
    }
  }

  async function remove() {
    if (busy.value) return false

    error.value = ''

    const userId = auth.user?.user_id

    if (userId == null) {
      error.value = 'Войдите в аккаунт, чтобы удалить музыку.'
      return false
    }

    operation.value = 'delete'

    try {
      await api('/users/me/music', {
        method: 'DELETE',
      })

      // DELETE возвращает 204. Дополнительный GET /users/me не нужен:
      // у него на бэкенде есть кэш, способный вернуть старую ссылку.
      updateMusicUrl(userId, null)

      return true
    } catch (cause) {
      if (isCurrentUser(userId)) {
        error.value = operationError(cause, 'delete')
      }

      return false
    } finally {
      operation.value = ''
    }
  }

  return {
    uploading,
    removing,
    busy,
    error,
    upload,
    remove,
  }
}
