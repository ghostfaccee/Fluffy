import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

const GROUPS_KEY = 'fluffy.groups'

function loadCachedGroups() {
  try {
    const raw = localStorage.getItem(GROUPS_KEY)
    if (!raw) return []

    const list = JSON.parse(raw)
    return Array.isArray(list) ? list : []
  } catch {
    return []
  }
}

function saveCachedGroups(list) {
  try {
    localStorage.setItem(GROUPS_KEY, JSON.stringify(list))
  } catch {}
}

function sameId(first, second) {
  return first != null && second != null && String(first) === String(second)
}

export const useGroupStore = defineStore('group', () => {
  const groups = ref(loadCachedGroups())
  const chats = ref({})
  const members = ref({})

  const historyRequests = new Map()

  // Объединяем запросы восстановления отправителей для одной группы.
  const senderSyncRequests = new Map()
  const pendingSenderSync = new Set()

  function persist() {
    saveCachedGroups(groups.value)
  }

  function upsertGroup(group) {
    let item = groups.value.find((entry) => entry.group_id === group.group_id)

    if (!item) {
      groups.value.unshift({ ...group })
    } else {
      Object.assign(item, group)
    }

    persist()
    return item
  }

  function removeGroup(groupId) {
    groups.value = groups.value.filter((group) => group.group_id !== groupId)

    persist()

    delete chats.value[groupId]
    delete members.value[groupId]
    pendingSenderSync.delete(String(groupId))
  }

  async function fetchGroups() {
    const list = await api('/groups')

    groups.value = Array.isArray(list) ? list : []
    persist()

    return groups.value
  }

  async function fetchGroup(groupId) {
    const group = await api(`/groups/${encodeURIComponent(groupId)}`)

    upsertGroup(group)
    return group
  }

  async function createGroup({ name, description }) {
    const group = await api('/groups', {
      method: 'POST',
      body: {
        name,
        description: description || null,
      },
    })

    upsertGroup(group)
    return group
  }

  async function updateGroup(groupId, data) {
    const group = await api(`/groups/${encodeURIComponent(groupId)}`, {
      method: 'PATCH',
      body: data,
    })

    upsertGroup(group)
    return group
  }

  async function deleteGroup(groupId) {
    await api(`/groups/${encodeURIComponent(groupId)}`, {
      method: 'DELETE',
    })

    removeGroup(groupId)
  }

  async function joinByToken(token) {
    const group = await api(`/groups/join/${encodeURIComponent(token)}`, {
      method: 'POST',
    })

    upsertGroup(group)
    return group
  }

  async function regenerateInviteToken(groupId) {
    const group = await api(
      `/groups/${encodeURIComponent(groupId)}/invite-token`,
      {
        method: 'POST',
      },
    )

    upsertGroup(group)
    return group
  }

  async function leaveGroup(groupId) {
    await api(`/groups/${encodeURIComponent(groupId)}/members/me`, {
      method: 'DELETE',
    })

    removeGroup(groupId)
  }

  async function kickMember(groupId, userId) {
    await api(
      `/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`,
      {
        method: 'DELETE',
      },
    )

    if (members.value[groupId]) {
      members.value[groupId] = members.value[groupId].filter(
        (member) => member.user_id !== userId,
      )
    }
  }

  async function changeRole(groupId, userId, role) {
    const result = await api(
      `/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}/change-role`,
      {
        method: 'PATCH',
        body: { role },
      },
    )

    if (members.value[groupId]) {
      const member = members.value[groupId].find(
        (entry) => entry.user_id === userId,
      )

      if (member) {
        member.role = result?.role || role
      }
    }

    return result
  }

  async function fetchMembers(groupId) {
    const list = await api(
      `/groups/${encodeURIComponent(groupId)}/members`,
    )

    members.value[groupId] = Array.isArray(list) ? list : []

    return members.value[groupId]
  }

  async function requestAvatarUploadUrl(groupId, contentType) {
    return await api(
      `/groups/${encodeURIComponent(groupId)}/avatar/upload-url`,
      {
        method: 'POST',
        body: { content_type: contentType },
      },
    )
  }

  async function setAvatar(groupId, key) {
    const group = await api(
      `/groups/${encodeURIComponent(groupId)}/avatar`,
      {
        method: 'PUT',
        body: { key },
      },
    )

    upsertGroup(group)
    return group
  }

  async function deleteAvatar(groupId) {
    await api(`/groups/${encodeURIComponent(groupId)}/avatar`, {
      method: 'DELETE',
    })

    const group = groups.value.find(
      (entry) => entry.group_id === groupId,
    )

    if (group) {
      group.avatar_url = null
      persist()
    }
  }

  async function loadChat(groupId, { limit = 30, offset = 0 } = {}) {
    const requestKey = `${groupId}:${limit}:${offset}`
    const existingRequest = historyRequests.get(requestKey)

    if (existingRequest) return existingRequest

    const chat = chats.value[groupId] || {
      messages: [],
      loading: false,
      hasMore: true,
    }

    chat.loading = true
    chats.value[groupId] = chat

    const request = (async () => {
      try {
        const list = await api(
          `/groups/${encodeURIComponent(groupId)}/messages?limit=${limit}&offset=${offset}`,
        )

        const safeList = Array.isArray(list) ? list : []
        const messages = [...safeList].reverse()

        if (offset === 0) {
          chat.messages = messages
        } else {
          chat.messages = [...messages, ...chat.messages]
        }

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

  function upsertMessage(chat, message) {
    const existing = chat.messages.find(
      (entry) => sameId(entry.message_id, message.message_id),
    )

    if (!existing) {
      chat.messages.push(message)
      return
    }

    // Событие без отправителя не должно стирать уже загруженный профиль.
    const sender = message.sender || existing.sender || null

    Object.assign(existing, message, { sender })
  }

  function findKnownSender(chat, senderId) {
    for (let index = chat.messages.length - 1; index >= 0; index -= 1) {
      const message = chat.messages[index]

      if (
        sameId(message.sender_id, senderId) &&
        message.sender &&
        (message.sender.username || message.sender.name)
      ) {
        return message.sender
      }
    }

    return null
  }

  function hasSenderProfile(sender) {
    return Boolean(sender && (sender.username || sender.name))
  }

  function syncMissingSenders(groupId) {
    const key = String(groupId)

    pendingSenderSync.add(key)

    if (senderSyncRequests.has(key)) {
      return senderSyncRequests.get(key)
    }

    const request = (async () => {
      try {
        while (pendingSenderSync.has(key)) {
          pendingSenderSync.delete(key)

          if (!chats.value[groupId]) break

          // Если история уже грузилась до нового события,
          // ждём её, затем запрашиваем актуальную версию.
          const historyKey = `${groupId}:30:0`
          const currentRequest = historyRequests.get(historyKey)

          if (currentRequest) {
            await currentRequest
          }

          if (!chats.value[groupId]) break

          await loadChat(groupId)
        }
      } catch (cause) {
        // Само сообщение уже отображается.
        // Ошибка подгрузки профиля не должна ломать WS-обработчик.
        console.error(
          'Не удалось загрузить отправителей сообщений группы:',
          cause,
        )
      } finally {
        pendingSenderSync.delete(key)
        senderSyncRequests.delete(key)
      }
    })()

    senderSyncRequests.set(key, request)

    return request
  }

  async function sendMessage(groupId, content) {
    const message = await api(
      `/groups/${encodeURIComponent(groupId)}/messages`,
      {
        method: 'POST',
        body: { content },
      },
    )

    const chat = chats.value[groupId] || {
      messages: [],
      loading: false,
      hasMore: true,
    }

    upsertMessage(chat, message)
    chats.value[groupId] = chat

    return message
  }

  function handleIncoming(payload) {
    const groupId = payload.group_id
    if (!groupId) return

    const chat = chats.value[groupId]
    if (!chat) return

    const sender = hasSenderProfile(payload.sender)
      ? payload.sender
      : findKnownSender(chat, payload.sender_id)

    upsertMessage(chat, {
      message_id: payload.message_id,
      group_id: groupId,
      sender_id: payload.sender_id,
      content: payload.content,
      created_at: payload.created_at,
      sender,
    })

    if (!hasSenderProfile(sender)) {
      void syncMissingSenders(groupId)
    }
  }

  return {
    groups,
    chats,
    members,
    upsertGroup,
    removeGroup,
    fetchGroups,
    fetchGroup,
    createGroup,
    updateGroup,
    deleteGroup,
    joinByToken,
    regenerateInviteToken,
    leaveGroup,
    kickMember,
    changeRole,
    fetchMembers,
    requestAvatarUploadUrl,
    setAvatar,
    deleteAvatar,
    loadChat,
    sendMessage,
    handleIncoming,
  }
})
