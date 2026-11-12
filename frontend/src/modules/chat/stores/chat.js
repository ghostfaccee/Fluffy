import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

const CONV_KEY = 'fluffy.conversations'

function sameId(first, second) {
  return (
    first != null &&
    second != null &&
    String(first) === String(second)
  )
}

function loadConversations() {
  try {
    const raw = localStorage.getItem(CONV_KEY)
    if (!raw) return []

    const list = JSON.parse(raw)
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

function saveConversations(list) {
  try {
    localStorage.setItem(CONV_KEY, JSON.stringify(list))
  } catch {}
}

function messageTime(message) {
  return Date.parse(message.created_at || '') || 0
}

export const useChatStore = defineStore('chat', () => {
  const auth = useAuthStore()

  const conversations = ref(loadConversations())
  const chats = ref({})

  const historyRequests = new Map()
  const readRequests = new Map()
  const pendingReadRequests = new Set()

  const visibleConversations = computed(() =>
    conversations.value.filter(
      (conversation) =>
        !sameId(conversation.user_id, auth.user?.user_id),
    ),
  )

  function persist() {
    saveConversations(conversations.value)
  }

  function findConversation(userId) {
    return conversations.value.find(
      (conversation) => sameId(conversation.user_id, userId),
    )
  }

  function sortConversations() {
    conversations.value.sort((first, second) => {
      const firstTime = Date.parse(first.lastMessageAt || '') || 0
      const secondTime = Date.parse(second.lastMessageAt || '') || 0

      return secondTime - firstTime
    })
  }

  function ensureChat(userId) {
    if (!chats.value[userId]) {
      chats.value[userId] = {
        messages: [],
        loading: false,
        hasMore: true,
      }
    }

    return chats.value[userId]
  }

  function upsertConversation(user, extra = {}) {
    if (!user?.user_id) return null
    if (sameId(user.user_id, auth.user?.user_id)) return null

    let item = findConversation(user.user_id)

    if (!item) {
      conversations.value.unshift({
        user_id: user.user_id,
        username: user.username || null,
        name: user.name || null,
        avatar_url: user.avatar_url || null,
        lastMessage: '',
        lastMessageAt: null,
        unread: 0,
      })

      item = findConversation(user.user_id)
    } else {
      if (user.username != null) item.username = user.username
      if (user.name != null) item.name = user.name

      if (
        Object.prototype.hasOwnProperty.call(user, 'avatar_url') &&
        user.avatar_url !== undefined
      ) {
        item.avatar_url = user.avatar_url
      }
    }

    Object.assign(item, extra)

    sortConversations()
    persist()

    return item
  }

  function removeConversation(userId) {
    conversations.value = conversations.value.filter(
      (conversation) => !sameId(conversation.user_id, userId),
    )

    persist()
  }

  function markConversationRead(userId) {
    const conversation = findConversation(userId)

    if (conversation) {
      conversation.unread = 0
      persist()
    }
  }

  function incrementUnread(userId) {
    const conversation = findConversation(userId)

    if (conversation) {
      conversation.unread = (Number(conversation.unread) || 0) + 1
      persist()
    }
  }

  function upsertMessage(chat, message) {
    const existing = chat.messages.find(
      (entry) => sameId(entry.message_id, message.message_id),
    )

    if (!existing) {
      chat.messages.push({ ...message })
      return chat.messages[chat.messages.length - 1]
    }

    const wasRead = existing.is_read === true
    const sender = message.sender || existing.sender || null
    const receiver = message.receiver || existing.receiver

    Object.assign(existing, message)

    existing.sender = sender

    if (receiver) {
      existing.receiver = receiver
    }

    // Запоздавший ответ истории не должен отменять прочтение.
    existing.is_read = wasRead || message.is_read === true

    return existing
  }

  function updateConversationFromHistory(userId, chat) {
    const existing = findConversation(userId)
    let otherUser = null

    for (let index = chat.messages.length - 1; index >= 0; index -= 1) {
      const message = chat.messages[index]

      if (sameId(message.sender?.user_id, userId)) {
        otherUser = message.sender
        break
      }

      if (sameId(message.receiver?.user_id, userId)) {
        otherUser = message.receiver
        break
      }
    }

    if (!chat.messages.length && !existing) return

    const last = chat.messages[chat.messages.length - 1]
    const extra = {}

    if (last) {
      const existingTime =
        Date.parse(existing?.lastMessageAt || '') || 0

      if (messageTime(last) >= existingTime) {
        extra.lastMessage = last.content
        extra.lastMessageAt = last.created_at
      }
    }

    upsertConversation(
      {
        user_id: userId,
        username: otherUser?.username ?? existing?.username ?? null,
        name: otherUser?.name ?? existing?.name ?? null,
        avatar_url: otherUser
          ? otherUser.avatar_url
          : existing?.avatar_url,
      },
      extra,
    )
  }

  async function loadChat(
    userId,
    { limit = 30, offset = 0 } = {},
  ) {
    const requestKey = `${userId}:${limit}:${offset}`
    const existingRequest = historyRequests.get(requestKey)

    if (existingRequest) return existingRequest

    const chat = ensureChat(userId)
    chat.loading = true

    const request = (async () => {
      try {
        const list = await api(
          `/messages/${encodeURIComponent(userId)}?limit=${limit}&offset=${offset}`,
        )

        if (chats.value[userId] !== chat) return chat

        const safeList = Array.isArray(list) ? list : []

        // Не теряем сообщения, пришедшие по WS во время запроса.
        for (const message of safeList) {
          upsertMessage(chat, message)
        }

        chat.messages.sort(
          (first, second) => messageTime(first) - messageTime(second),
        )

        chat.hasMore = safeList.length === limit

        updateConversationFromHistory(userId, chat)

        return chat
      } finally {
        historyRequests.delete(requestKey)

        const prefix = `${userId}:`
        chat.loading = [...historyRequests.keys()].some(
          (key) => key.startsWith(prefix),
        )
      }
    })()

    historyRequests.set(requestKey, request)

    return request
  }

  async function sendMessage(receiverId, content) {
    const message = await api(
      `/messages/${encodeURIComponent(receiverId)}`,
      {
        method: 'POST',
        body: { content },
      },
    )

    const chat = ensureChat(receiverId)
    upsertMessage(chat, message)

    chat.messages.sort(
      (first, second) => messageTime(first) - messageTime(second),
    )

    const existing = findConversation(receiverId)

    const receiver = sameId(message.receiver?.user_id, receiverId)
      ? message.receiver
      : null

    upsertConversation(
      {
        user_id: receiverId,
        username: receiver?.username ?? existing?.username ?? null,
        name: receiver?.name ?? existing?.name ?? null,
        avatar_url: receiver
          ? receiver.avatar_url
          : existing?.avatar_url,
      },
      {
        lastMessage: message.content ?? content,
        lastMessageAt:
          message.created_at || new Date().toISOString(),
      },
    )

    return message
  }

  async function markRead(senderId) {
    const key = String(senderId)

    pendingReadRequests.add(key)

    const existingRequest = readRequests.get(key)
    if (existingRequest) return existingRequest

    const request = (async () => {
      try {
        while (pendingReadRequests.has(key)) {
          pendingReadRequests.delete(key)

          const chat = chats.value[senderId]
          const conversation = findConversation(senderId)

          // Запоминаем только сообщения, известные до запроса.
          const unreadIds = new Set(
            (chat?.messages || [])
              .filter(
                (message) =>
                  sameId(message.sender_id, senderId) &&
                  message.is_read !== true,
              )
              .map((message) => String(message.message_id)),
          )

          const unreadBefore =
            Number(conversation?.unread) || 0

          await api(
            `/messages/${encodeURIComponent(senderId)}/read`,
            { method: 'POST' },
          )

          if (chat) {
            for (const message of chat.messages) {
              if (
                sameId(message.sender_id, senderId) &&
                unreadIds.has(String(message.message_id))
              ) {
                message.is_read = true
              }
            }
          }

          const currentConversation = findConversation(senderId)

          if (currentConversation) {
            // Новые сообщения, пришедшие во время запроса,
            // не сбрасываем вместе со старыми.
            currentConversation.unread = Math.max(
              0,
              (Number(currentConversation.unread) || 0) -
                unreadBefore,
            )

            persist()
          }
        }
      } finally {
        pendingReadRequests.delete(key)
        readRequests.delete(key)
      }
    })()

    readRequests.set(key, request)

    return request
  }

  function handleIncoming(payload) {
    const senderId = payload.sender_id

    if (senderId == null) return
    if (sameId(senderId, auth.user?.user_id)) return

    const existingConversation = findConversation(senderId)
    const chat = ensureChat(senderId)

    const duplicate = chat.messages.some(
      (message) => sameId(message.message_id, payload.message_id),
    )

    const sender = sameId(payload.sender?.user_id, senderId)
      ? payload.sender
      : existingConversation
        ? {
            user_id: existingConversation.user_id,
            username: existingConversation.username,
            name: existingConversation.name,
            avatar_url: existingConversation.avatar_url,
          }
        : null

    upsertMessage(chat, {
      message_id: payload.message_id,
      sender_id: senderId,
      content: payload.content,
      created_at: payload.created_at,
      is_read: payload.is_read === true,
      sender,
    })

    chat.messages.sort(
      (first, second) => messageTime(first) - messageTime(second),
    )

    const extra = {
      unread:
        (Number(existingConversation?.unread) || 0) +
        (duplicate || payload.is_read === true ? 0 : 1),
    }

    const incomingTime = Date.parse(payload.created_at || '') || 0
    const existingTime =
      Date.parse(existingConversation?.lastMessageAt || '') || 0

    if (!existingConversation || incomingTime >= existingTime) {
      extra.lastMessage = payload.content
      extra.lastMessageAt = payload.created_at
    }

    upsertConversation(sender || { user_id: senderId }, extra)

    // Наличие чата в памяти не означает, что пользователь его видит.
    // Прочтение подтверждает только открытая страница диалога.
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
