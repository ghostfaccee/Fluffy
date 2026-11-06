const BASE = '/v1'
const REFRESH_KEY = 'refresh_token'
const ACCESS_KEY = 'access_token'
const ACCESS_EXPIRY_KEY = 'access_token_expires_at'
const EXPIRY_SKEW_MS = 60_000

// Keep the short-lived access token for this tab across reloads. Without this,
// every reload loses it and forces a refresh-token rotation.
let accessToken = sessionStorage.getItem(ACCESS_KEY) || null
let accessTokenExpiresAt = Number(sessionStorage.getItem(ACCESS_EXPIRY_KEY)) || 0
let sessionExpiredHandler = () => {}
let refreshPromise = null
let refreshBlockedUntil = 0

export class APIError extends Error {
  constructor(status, detail, retryAfter = null) {
    super(typeof detail === 'string' ? detail : 'Request failed')
    this.status = status
    this.detail = detail
    this.retryAfter = retryAfter
  }
}

export function setSessionExpiredHandler(handler) {
  sessionExpiredHandler = handler
}

export function setTokens(tokens) {
  const { access_token, refresh_token, access_token_expire_minutes } = tokens
  accessToken = access_token
  // The API returns the configured lifetime. JWT exp is a fallback for older servers.
  let expiresAt = 0
  try {
    const payload = JSON.parse(atob(access_token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')))
    if (Number.isFinite(payload.exp)) expiresAt = payload.exp * 1000
  } catch {}
  if (!expiresAt && Number.isFinite(access_token_expire_minutes)) {
    expiresAt = Date.now() + access_token_expire_minutes * 60_000
  }
  accessTokenExpiresAt = expiresAt || Date.now() + (access_token_expire_minutes || 5) * 60_000
  if (accessToken) sessionStorage.setItem(ACCESS_KEY, accessToken)
  sessionStorage.setItem(ACCESS_EXPIRY_KEY, String(accessTokenExpiresAt))
  if (refresh_token) localStorage.setItem(REFRESH_KEY, refresh_token)
}

export function clearTokens() {
  accessToken = null
  accessTokenExpiresAt = 0
  sessionStorage.removeItem(ACCESS_KEY)
  sessionStorage.removeItem(ACCESS_EXPIRY_KEY)
  localStorage.removeItem(REFRESH_KEY)
}

export function hasRefreshToken() {
  return localStorage.getItem(REFRESH_KEY) !== null
}

export function hasUsableAccessToken() {
  return Boolean(accessToken && accessTokenExpiresAt - Date.now() > EXPIRY_SKEW_MS)
}

async function doRefresh() {
  if (Date.now() < refreshBlockedUntil) {
    throw new APIError(429, 'Слишком много запросов обновления. Повторите позже.')
  }
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

  if (res.status === 429) {
    const seconds = Number(res.headers.get('Retry-After'))
    refreshBlockedUntil = Date.now() + (Number.isFinite(seconds) && seconds > 0 ? seconds * 1000 : 60_000)
    throw new APIError(429, 'Слишком много запросов. Повторите позже.', res.headers.get('Retry-After'))
  }
  if (!res.ok) {
    // Only definitive authentication failures invalidate the stored refresh token.
    if ([400, 401, 403].includes(res.status)) clearTokens()
    return false
  }
  setTokens(await res.json())
  refreshBlockedUntil = 0
  return true
}

export function refreshTokens() {
  if (!refreshPromise) {
    refreshPromise = doRefresh().finally(() => {
      refreshPromise = null
    })
  }
  return refreshPromise
}

async function ensureFreshAccessToken() {
  if (hasUsableAccessToken()) return true
  return refreshTokens()
}

export async function refreshSession() {
  return refreshTokens()
}

export async function api(path, { method = 'GET', body, auth = true } = {}, retried = false) {
  if (auth && !retried && hasRefreshToken()) {
    await ensureFreshAccessToken()
  }

  const requestToken = accessToken
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
    // Another request may already have rotated the refresh token while this one was in flight.
    // In that case replay with the newer access token instead of rotating again.
    const refreshed = accessToken !== requestToken
      ? true
      : await refreshTokens()
    if (refreshed) return api(path, { method, body, auth }, true)
    sessionExpiredHandler()
  }

  if (!res.ok) {
    let detail = res.statusText
    try { detail = (await res.json()).detail ?? detail } catch {}
    throw new APIError(res.status, detail, res.headers.get('Retry-After'))
  }

  if (res.status === 204) return null
  return res.json()
}

export function getAccessToken() {
  return accessToken
}
