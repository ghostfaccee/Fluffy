import { defineStore } from 'pinia'
import { api, setTokens, clearTokens, hasRefreshToken, hasUsableAccessToken } from '@/api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
  }),

  getters: {
    isAuthenticated: (state) => state.user !== null,
  },

  actions: {
    setUser(user) {
      this.user = user
    },

    async requestLoginCode(username, password) {
      await api('/auth/login', { method: 'POST', auth: false, body: { username, password } })
    },

    async confirmLoginCode(username, code) {
      const tokens = await api(
        `/auth/login/verify/${encodeURIComponent(username)}`,
        { method: 'POST', auth: false, body: { code } },
      )
      setTokens(tokens)
      this.user = await api('/users/me')
    },

    async register(payload) {
      return await api('/users', { method: 'POST', auth: false, body: payload })
    },

    async fetchMe() {
      const user = await api('/users/me')
      this.setUser(user)
      return user
    },

    async fetchUserByUsername(username) {
      return await api(`/users/${encodeURIComponent(username)}`)
    },

    async updateProfile(data) {
      const user = await api('/users/me', { method: 'PATCH', body: data })
      this.setUser(user)
      return user
    },

    async updatePassword({ old_password, new_password }) {
      const user = await api('/users/me/password', {
        method: 'PATCH',
        body: { old_password, new_password },
      })
      this.setUser(user)
      return user
    },

    async deleteAccount() {
      await api('/users/me', { method: 'DELETE' })
      clearTokens()
      this.user = null
    },

    async restoreSession() {
      if (!hasRefreshToken() && !hasUsableAccessToken()) return
      try {
        // api() refreshes only when the cached access token is missing or near expiry.
        // A still-valid token survives a page reload via sessionStorage.
        this.user = await api('/users/me')
      } catch (error) {
        // A rate limit or network outage is temporary: never destroy the session.
        if (error?.status !== 429 && error?.status !== 0) {
          clearTokens()
          this.user = null
        }
      }
    },

    async logout() {
      try {
        await api('/auth/logout', { method: 'POST' })
      } catch {
      } finally {
        clearTokens()
        this.user = null
      }
    },
  },
})
