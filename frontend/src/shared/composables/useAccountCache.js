import { watch } from 'vue'
import { api } from '@/shared/api/client'
import { useAuthStore } from '@/modules/auth/stores/auth'

function normalizeId(value) {
  return value == null ? null : String(value)
}

function readList(key) {
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return []

    const value = JSON.parse(raw)
    return Array.isArray(value) ? value : []
  } catch {
    return []
  }
}

function sessionChangedError() {
  const error = new Error(
    'Аккаунт изменился. Результат старого запроса отменён.',
  )

  error.name = 'AbortError'
  error.code = 'SESSION_CHANGED'

  return error
}

export function useAccountCache(baseKey, reset) {
  const auth = useAuthStore()

  let ownerId = null
  let revision = 0

  // У общего старого кеша нет достоверного владельца.
  // Переносить его в кеш текущего аккаунта небезопасно.
  try {
    localStorage.removeItem(baseKey)
  } catch {}

  function cacheKey() {
    return `${baseKey}:${encodeURIComponent(ownerId)}`
  }

  function current(ticket) {
    return (
      ownerId !== null &&
      ticket === revision &&
      ownerId === normalizeId(auth.user?.user_id)
    )
  }

  function assertCurrent(ticket) {
    if (!current(ticket)) {
      throw sessionChangedError()
    }
  }

  function persist(list) {
    if (ownerId === null) return

    try {
      localStorage.setItem(cacheKey(), JSON.stringify(list))
    } catch {}
  }

  async function request(path, options, commit) {
    const ticket = revision

    assertCurrent(ticket)

    let result

    try {
      result = await api(path, options)
    } catch (error) {
      assertCurrent(ticket)
      throw error
    }

    assertCurrent(ticket)

    // Изменение store выполняется синхронно после проверки
    // владельца и поколения сессии.
    return commit ? commit(result) : result
  }

  watch(
    () => normalizeId(auth.user?.user_id),
    (nextId) => {
      revision += 1
      ownerId = nextId

      const cached = ownerId === null
        ? []
        : readList(cacheKey())

      reset(cached)
    },
    {
      immediate: true,
      flush: 'sync',
    },
  )

  return {
    active: () => ownerId !== null,
    ticket: () => revision,
    current,
    assertCurrent,
    persist,
    request,
  }
}
