const BASE = '/v1'
const REFRESH_KEY = 'refresh_token'

let accessToken = null
let sessionExpiredHandler = () => {}

export class APIError extends Error {
  constructor(status, detail) {
    super(typeof detail === 'string' ? detail : 'Request failed')
    this.status = status
    this.detail = detail
  }
}

export function setSessionExpiredHandler(handler) {
  sessionExpiredHandler = handler
}

export function setTokens({ access_token, refresh_token }) {
  accessToken = access_token
  localStorage.setItem(REFRESH_KEY, refresh_token)
}

export function clearTokens() {
  accessToken = null
  localStorage.removeItem(REFRESH_KEY)
}

export function hasRefreshToken() {
  return localStorage.getItem(REFRESH_KEY) !== null
}

async function doRefresh() {
  const refreshToken = localStorage.getItem(REFRESH_KEY)
  if (!refreshToken) return false

  let res
  try {
    res = await fetch(`${BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    })
  } catch {
    throw new APIError(0, 'Нет связи с сервером')
  }

  if (!res.ok) {
    clearTokens()
    return false
  }

  setTokens(await res.json())
  return true
}

let refreshPromise = null

function refreshTokens() {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

export async function api(path, { method = 'GET', body, auth = true } = {}, retried = false) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (auth && accessToken) headers.Authorization = `Bearer ${accessToken}`

  let res
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    })
  } catch {
    throw new APIError(0, 'Нет связи с сервером')
  }

  if (res.status === 401 && auth && !retried) {
    if (await refreshTokens()) {
      return api(path, { method, body, auth }, true)
    }
    sessionExpiredHandler()
  }

  if (!res.ok) {
    let detail = res.statusText
    try {
      detail = (await res.json()).detail ?? detail
    } catch {}
    throw new APIError(res.status, detail)
  }

  if (res.status === 204) return null
  return res.json()
}