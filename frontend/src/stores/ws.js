import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { getAccessToken } from '@/api/client'

const SUBPROTOCOL = 'fluffy'
const BEARER_PREFIX = 'bearer.'
const PING_INTERVAL = 30000
const MAX_BACKOFF = 30000

export const useWsStore = defineStore('ws', () => {
  const connected = ref(false)
  const listeners = new Map()

  let socket = null
  let pingTimer = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  let manuallyClosed = false

  function wsUrl() {
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:'
    return `${proto}//${location.host}/v1/ws`
  }

  function connect() {
    manuallyClosed = false
    if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
      return
    }
    const token = getAccessToken()
    if (!token) return

    socket = new WebSocket(wsUrl(), [SUBPROTOCOL, `${BEARER_PREFIX}${token}`])

    socket.addEventListener('open', () => {
      connected.value = true
      reconnectAttempts = 0
      startPing()
    })

    socket.addEventListener('message', (event) => {
      let data
      try {
        data = JSON.parse(event.data)
      } catch {
        return
      }
      if (data?.type === 'pong') return
      const type = data?.type
      if (!type) return
      const set = listeners.get(type)
      if (set) {
        for (const fn of set) {
          try { fn(data) } catch (e) { console.error('WS listener error:', e) }
        }
      }
    })

    socket.addEventListener('close', () => {
      connected.value = false
      stopPing()
      if (!manuallyClosed) scheduleReconnect()
    })

    socket.addEventListener('error', () => {
      try { socket.close() } catch {}
    })
  }

  function disconnect() {
    manuallyClosed = true
    stopPing()
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (socket) {
      try { socket.close() } catch {}
      socket = null
    }
    connected.value = false
  }

  function send(data) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(data))
    }
  }

  function on(type, fn) {
    if (!listeners.has(type)) listeners.set(type, new Set())
    listeners.get(type).add(fn)
    return () => off(type, fn)
  }

  function off(type, fn) {
    const set = listeners.get(type)
    if (set) set.delete(fn)
  }

  function startPing() {
    stopPing()
    pingTimer = setInterval(() => {
      send({ type: 'ping' })
    }, PING_INTERVAL)
  }

  function stopPing() {
    if (pingTimer) {
      clearInterval(pingTimer)
      pingTimer = null
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    const delay = Math.min(1000 * 2 ** reconnectAttempts, MAX_BACKOFF)
    reconnectAttempts += 1
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      connect()
    }, delay)
  }

  return { connected, connect, disconnect, send, on, off }
})