import { ref } from 'vue'
import { api } from '@/api/client'
import { useGroupStore } from '@/stores/group'

const MAX_SIZE = 5 * 1024 * 1024
const ALLOWED = ['image/jpeg', 'image/png']

function normalizeType(type) {
  if (type === 'image/jpg') return 'image/jpeg'
  return type
}

export function useGroupAvatarUpload(groupIdRef) {
  const groupStore = useGroupStore()
  const uploading = ref(false)
  const error = ref('')

  async function upload(file) {
    error.value = ''
    if (!file || !groupIdRef.value) return

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
      const { upload_url, key } = await groupStore.requestAvatarUploadUrl(groupIdRef.value, contentType)

      let res
      try {
        res = await fetch(upload_url, {
          method: 'PUT',
          headers: { 'Content-Type': contentType },
          body: file,
        })
      } catch (networkErr) {
        console.error('S3 PUT network error:', networkErr, 'url:', upload_url)
        error.value = 'Не удалось связаться с хранилищем (CORS или сеть).'
        throw networkErr
      }

      if (!res.ok) {
        console.error('S3 PUT failed:', res.status)
        error.value = res.status === 403
          ? 'Хранилище отклонило запрос (403).'
          : 'Хранилище вернуло ошибку ' + res.status + '.'
        throw new Error('S3 ' + res.status)
      }

      await groupStore.setAvatar(groupIdRef.value, key)
    } catch (e) {
      if (!error.value) {
        if (e?.status === 0) error.value = 'Нет связи с сервером.'
        else if (e?.status === 403) error.value = 'Недостаточно прав.'
        else error.value = 'Не удалось установить аватар группы.'
      }
      throw e
    } finally {
      uploading.value = false
    }
  }

  async function remove() {
    error.value = ''
    if (!groupIdRef.value) return
    uploading.value = true
    try {
      await groupStore.deleteAvatar(groupIdRef.value)
    } catch {
      error.value = 'Не удалось удалить аватар группы.'
    } finally {
      uploading.value = false
    }
  }

  return { uploading, error, upload, remove }
}