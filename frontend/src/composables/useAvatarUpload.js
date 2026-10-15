import { ref } from 'vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const MAX_SIZE = 5 * 1024 * 1024
const ALLOWED = ['image/jpeg', 'image/png']

function normalizeType(type) {
  if (type === 'image/jpg') return 'image/jpeg'
  return type
}

export function useAvatarUpload() {
  const auth = useAuthStore()
  const uploading = ref(false)
  const error = ref('')

  async function upload(file) {
    error.value = ''
    if (!file) return

    const contentType = normalizeType(file.type)
    if (!ALLOWED.includes(contentType)) {
      error.value = 'Можно загрузить только JPEG или PNG.'
      return
    }
    if (file.size > MAX_SIZE) {
      error.value = 'Файл слишком большой (макс. 5 МБ).'
      return
    }

    uploading.value = true
    try {
      const { upload_url, key } = await api('/users/me/avatar/upload-url', {
        method: 'POST',
        body: { content_type: contentType },
      })

      const res = await fetch(upload_url, {
        method: 'PUT',
        headers: { 'Content-Type': contentType },
        body: file,
      })
      if (!res.ok) {
        throw new Error('S3 upload failed: ' + res.status)
      }

      const user = await api('/users/me/avatar', {
        method: 'PUT',
        body: { key },
      })
      auth.setUser(user)
    } catch (e) {
      if (e?.status === 0) error.value = 'Нет связи с сервером.'
      else if (e?.status === 422) error.value = 'Неверный формат файла.'
      else if (e?.status === 413) error.value = 'Файл слишком большой.'
      else if (e?.status === undefined) error.value = 'Не удалось загрузить файл в хранилище.'
      else error.value = 'Не удалось установить аватар.'
      throw e
    } finally {
      uploading.value = false
    }
  }

  async function remove() {
    error.value = ''
    uploading.value = true
    try {
      await api('/users/me/avatar', { method: 'DELETE' })
      const user = await api('/users/me')
      auth.setUser(user)
    } catch {
      error.value = 'Не удалось удалить аватар.'
    } finally {
      uploading.value = false
    }
  }

  return { uploading, error, upload, remove }
}