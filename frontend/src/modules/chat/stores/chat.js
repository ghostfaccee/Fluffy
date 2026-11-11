import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const CONV_KEY = 'fluffy.conversations'

function loadConversations() {
  try {
    const raw = localStorage.getItem(CONV_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

function saveConversations(list) {
  try {
    localStorage.setItem(CONV_KEY, JSON.stringify(list))
  } catch {}
}

export const useChatStore = defineStore('chat', () => {
  const auth = useAuthStore()

  const conversations = ref(loadConversations())
  const chats = ref({})
  const historyRequests = new Map()
  const readRequests = new Map()
  const lastReadAt = new Map()

  const visibleConversations = computed(() =>
    conversations.value.filter((c) => c.user_id !== auth.user?.user_id)
  )

  function persist() {
    saveConversations(conversations.value)
  }

  function upsertConversation(user, extra = {}) {
    if (!user || !user.user_id) return null
    if (user.user_id === auth.user?.user_id) return null

    let item = conversations.value.find((c) => c.user_id === user.user_id)
    if (!item) {
      item = {
        user_id: user.user_id,
        username: user.username || null,
        name: user.name || null,
        avatar_url: user.avatar_url || null,
        lastMessage: '',
        lastMessageAt: null,
        unread: 0,
      }
      conversations.value.unshift(item)
    } else {
      item.username = user.username || item.username
      item.name = user.name || item.name
      item.avatar_url = user.avatar_url || item.avatar_url
    }
    Object.assign(item, extra)
    conversations.value.sort((a, b) => {
      const ta = a.lastMessageAt ? Date.parse(a.lastMessageAt) : 0
      const tb = b.lastMessageAt ? Date.parse(b.lastMessageAt) : 0
      return tb - ta
    })
    persist()
    return item
  }

  function removeConversation(userId) {
    conversations.value = conversations.value.filter((c) => c.user_id !== userId)
    persist()
  }

  function markConversationRead(userId) {
    const c = conversations.value.find((x) => x.user_id === userId)
    if (c) {
      c.unread = 0
      persist()
    }
  }

  function incrementUnread(userId) {
    const c = conversations.value.find((x) => x.user_id === userId)
    if (c) {
      c.unread = (c.unread || 0) + 1
      persist()
    }
  }

  async function loadChat(userId, { limit = 30, offset = 0 } = {}) {
    const requestKey = `${userId}:${limit}:${offset}`
    const existingRequest = historyRequests.get(requestKey)
    if (existingRequest) return existingRequest

    const chat = chats.value[userId] || { messages: [], loading: false, hasMore: true }
    chat.loading = true
    chats.value[userId] = chat

    const request = (async () => {
      try {
        const list = await api(`/messages/${encodeURIComponent(userId)}?limit=${limit}&offset=${offset}`)
        const safeList = Array.isArray(list) ? list : []
        const messages = [...safeList].reverse()
        if (offset === 0) chat.messages = messages
        else chat.messages = [...messages, ...chat.messages]
        chat.hasMore = safeList.length === limit
      } finally {
        chat.loading = false
        historyRequests.delete(requestKey)
      }
      return chat
    })()

    historyRequests.set(requestKey, request)
    return request
  }

    async function sendMessage(receiverId, content) {
    const msg = await api(`/messages/${encodeURIComponent(receiverId)}`, {
      method: 'POST',
      body: { content },
    })

    const chat = chats.value[receiverId] || {
      messages: [],
      loading: false,
      hasMore: true,
    }

    const alreadyExists =
      msg.message_id != null &&
      chat.messages.some((item) => item.message_id === msg.message_id)

    if (!alreadyExists) {
      chat.messages.push(msg)
    }

    chats.value[receiverId] = chat

    // Диалог создаём с получателем, а не с отправителем.
    const existing = conversations.value.find(
      (item) => String(item.user_id) === String(receiverId),
    )

    const receiver =
      msg.receiver &&
      String(msg.receiver.user_id) === String(receiverId)
        ? msg.receiver
        : null

    upsertConversation(
      {
        user_id: receiverId,
        username: receiver?.username || existing?.username || null,
        name: receiver?.name || existing?.name || null,
        avatar_url: receiver?.avatar_url || existing?.avatar_url || null,
      },
      {
        lastMessage: msg.content ?? content,
        lastMessageAt: msg.created_at || new Date().toISOString(),
      },
    )

    return msg
  }

  async function markRead(senderId) {
    const inFlight = readRequests.get(senderId)
    if (inFlight) return inFlight

    // Coalesce repeated WS notifications: do not POST read-state for every message.
    const lastSent = lastReadAt.get(senderId) || 0
    if (Date.now() - lastSent < 10000) {
      markConversationRead(senderId)
      return
    }

    const request = (async () => {
      try {
        await api(`/messages/${encodeURIComponent(senderId)}/read`, { method: 'POST' })
        lastReadAt.set(senderId, Date.now())
        markConversationRead(senderId)
      } catch {
        // A later open/message event can retry the read receipt.
      } finally {
        readRequests.delete(senderId)
      }
    })()

    readRequests.set(senderId, request)
    return request
  }

  function handleIncoming(payload) {
    const senderId = payload.sender_id
    const myId = auth.user?.user_id
    if (senderId === myId) return

    const conv = conversations.value.find((c) => c.user_id === senderId)
    const chat = chats.value[senderId]

    if (chat) {
      chat.messages.push({
        message_id: payload.message_id,
        sender_id: senderId,
        content: payload.content,
        is_read: true,
        created_at: payload.created_at,
        sender: conv
          ? { user_id: conv.user_id, username: conv.username, name: conv.name, avatar_url: conv.avatar_url }
          : null,
      })
    }

    if (conv) {
      conv.lastMessage = payload.content
      conv.lastMessageAt = payload.created_at
      if (!chat) conv.unread = (conv.unread || 0) + 1
      persist()
    } else {
      conversations.value.unshift({
        user_id: senderId,
        username: null,
        name: null,
        avatar_url: null,
        lastMessage: payload.content,
        lastMessageAt: payload.created_at,
        unread: 1,
      })
      persist()
    }

    if (chat) {
      markRead(senderId)
    }
  }

  return {
    conversations,
    visibleConversations,
    chats,
    upsertConversation,
    removeConversation,
    markConversationRead,
    incrementUnread,
    loadChat,
    sendMessage,
    markRead,
    handleIncoming,
  }
})
