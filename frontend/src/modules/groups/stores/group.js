import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/shared/api/client'

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
  return (
    first != null &&
    second != null &&
    String(first) === String(second)
  )
}

export const useGroupStore = defineStore('group', () => {
  const groups = ref(loadCachedGroups())
  const chats = ref({})
  const members = ref({})

  const historyRequests = new Map()
  const senderSyncRequests = new Map()
  const pendingSenderSync = new Set()

  function persist() {
    saveCachedGroups(groups.value)
  }

  function upsertGroup(group) {
    const existing = groups.value.find(
      (entry) => sameId(entry.group_id, group.group_id),
    )

    if (existing) {
      Object.assign(existing, group)
    } else {
      groups.value.unshift({ ...group })
    }

    persist()

    return groups.value.find(
      (entry) => sameId(entry.group_id, group.group_id),
    )
  }

  function removeGroup(groupId) {
    groups.value = groups.value.filter(
      (group) => !sameId(group.group_id, groupId),
    )

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
    const group = await api(
      `/groups/${encodeURIComponent(groupId)}`,
    )

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
    const group = await api(
      `/groups/${encodeURIComponent(groupId)}`,
      {
        method: 'PATCH',
        body: data,
      },
    )

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
    const group = await api(
      `/groups/join/${encodeURIComponent(token)}`,
      {
        method: 'POST',
      },
    )

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
    await api(
      `/groups/${encodeURIComponent(groupId)}/members/me`,
      {
        method: 'DELETE',
      },
    )

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
        (member) => !sameId(member.user_id, userId),
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

    const member = members.value[groupId]?.find(
      (entry) => sameId(entry.user_id, userId),
    )

    if (member) {
      member.role = result?.role || role
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
    await api(
      `/groups/${encodeURIComponent(groupId)}/avatar`,
      {
        method: 'DELETE',
      },
    )

    const group = groups.value.find(
      (entry) => sameId(entry.group_id, groupId),
    )

    if (group) {
      group.avatar_url = null
      persist()
    }
  }

  function hasSenderProfile(sender) {
    return Boolean(sender && (sender.username || sender.name))
  }

  function ensureChat(groupId) {
    if (!chats.value[groupId]) {
      chats.value[groupId] = {
        messages: [],
        loading: false,
        hasMore: true,
      }
    }

    // Все дальнейшие изменения идут через реактивный объект.
    return chats.value[groupId]
  }

  function findKnownSender(chat, senderId) {
    for (
      let index = chat.messages.length - 1;
      index >= 0;
      index -= 1
    ) {
      const message = chat.messages[index]

      if (
        sameId(message.sender_id, senderId) &&
        hasSenderProfile(message.sender)
      ) {
        return message.sender
      }
    }

    return null
  }

  function upsertMessage(chat, message) {
    const existing = chat.messages.find(
      (entry) => sameId(entry.message_id, message.message_id),
    )

    const sender = hasSenderProfile(message.sender)
      ? message.sender
      : (
          hasSenderProfile(existing?.sender)
            ? existing.sender
            : findKnownSender(chat, message.sender_id)
        )

    if (existing) {
      Object.assign(existing, message, {
        sender: sender || null,
      })

      return existing
    }

    chat.messages.push({
      ...message,
      sender: sender || null,
    })

    return chat.messages[chat.messages.length - 1]
  }

  async function loadChat(
    groupId,
    { limit = 30, offset = 0 } = {},
  ) {
    const requestKey = `${groupId}:${limit}:${offset}`
    const existingRequest = historyRequests.get(requestKey)

    if (existingRequest) return existingRequest

    const chat = ensureChat(groupId)
    chat.loading = true

    const request = (async () => {
      try {
        const list = await api(
          `/groups/${encodeURIComponent(groupId)}/messages?limit=${limit}&offset=${offset}`,
        )

        // За время запроса пользователь мог покинуть группу.
        if (chats.value[groupId] !== chat) return chat

        const safeList = Array.isArray(list) ? list : []

        // Объединяем историю с сообщениями, полученными по WS,
        // а не заменяем весь массив.
        for (const message of [...safeList].reverse()) {
          upsertMessage(chat, message)
        }

        const profiles = new Map()

        for (const message of chat.messages) {
          if (
            message.sender_id != null &&
            hasSenderProfile(message.sender)
          ) {
            profiles.set(
              String(message.sender_id),
              message.sender,
            )
          }
        }

        // Профиль из REST дополняет сообщения того же автора,
        // которые пришли по WS без sender.
        for (const message of chat.messages) {
          if (
            message.sender_id != null &&
            !hasSenderProfile(message.sender)
          ) {
            const sender = profiles.get(
              String(message.sender_id),
            )

            if (sender) {
              message.sender = sender
            }
          }
        }

        chat.messages.sort((first, second) => {
          const firstTime =
            Date.parse(first.created_at || '') || 0

          const secondTime =
            Date.parse(second.created_at || '') || 0

          return firstTime - secondTime
        })

        chat.hasMore = safeList.length === limit

        return chat
      } finally {
        chat.loading = false
        historyRequests.delete(requestKey)
      }
    })()

    historyRequests.set(requestKey, request)

    return request
  }

  function syncMissingSenders(groupId) {
    const key = String(groupId)

    pendingSenderSync.add(key)

    const existingRequest = senderSyncRequests.get(key)

    if (existingRequest) return existingRequest

    const request = (async () => {
      try {
        while (pendingSenderSync.has(key)) {
          pendingSenderSync.delete(key)

          const chat = chats.value[groupId]
          if (!chat) break

          // Старый запрос мог начаться до входящего сообщения.
          // Сначала ждём его, затем запрашиваем свежую историю.
          const currentRequest = historyRequests.get(
            `${groupId}:30:0`,
          )

          if (currentRequest) {
            await currentRequest
          }

          if (chats.value[groupId] !== chat) break

          await loadChat(groupId)
        }
      } catch (cause) {
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

    const chat = ensureChat(groupId)

    upsertMessage(chat, message)

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

    const message = upsertMessage(chat, {
      message_id: payload.message_id,
      group_id: groupId,
      sender_id: payload.sender_id,
      content: payload.content,
      created_at: payload.created_at,
      sender,
    })

    if (!hasSenderProfile(message.sender)) {
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
