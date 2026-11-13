import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useAccountCache } from '@/shared/composables/useAccountCache'

const GROUPS_KEY = 'fluffy.groups'

function sameId(first, second) {
  return (
    first != null &&
    second != null &&
    String(first) === String(second)
  )
}

export const useGroupStore = defineStore('group', () => {
  const groups = ref([])
  const chats = ref({})
  const members = ref({})

  const historyRequests = new Map()
  const senderSyncRequests = new Map()
  const pendingSenderSync = new Set()

  const account = useAccountCache(GROUPS_KEY, (cached) => {
    groups.value = cached
    chats.value = {}
    members.value = {}

    historyRequests.clear()
    senderSyncRequests.clear()
    pendingSenderSync.clear()
  })

  function persist() {
    account.persist(groups.value)
  }

  function upsertGroup(group) {
    if (!account.active()) return null
    if (group?.group_id == null) return null

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
    if (!account.active()) return

    groups.value = groups.value.filter(
      (group) => !sameId(group.group_id, groupId),
    )

    persist()

    delete chats.value[groupId]
    delete members.value[groupId]
    pendingSenderSync.delete(String(groupId))
  }

  async function fetchGroups() {
    return await account.request(
      '/groups',
      undefined,
      (list) => {
        groups.value = Array.isArray(list) ? list : []
        persist()

        return groups.value
      },
    )
  }

  async function fetchGroup(groupId) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}`,
      undefined,
      (group) => {
        upsertGroup(group)
        return group
      },
    )
  }

  async function createGroup({ name, description }) {
    return await account.request(
      '/groups',
      {
        method: 'POST',
        body: {
          name,
          description: description || null,
        },
      },
      (group) => {
        upsertGroup(group)
        return group
      },
    )
  }

  async function updateGroup(groupId, data) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}`,
      {
        method: 'PATCH',
        body: data,
      },
      (group) => {
        upsertGroup(group)
        return group
      },
    )
  }

  async function deleteGroup(groupId) {
    await account.request(
      `/groups/${encodeURIComponent(groupId)}`,
      { method: 'DELETE' },
      () => {
        removeGroup(groupId)
      },
    )
  }

  async function joinByToken(token) {
    return await account.request(
      `/groups/join/${encodeURIComponent(token)}`,
      { method: 'POST' },
      (group) => {
        upsertGroup(group)
        return group
      },
    )
  }

  async function regenerateInviteToken(groupId) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}/invite-token`,
      { method: 'POST' },
      (group) => {
        upsertGroup(group)
        return group
      },
    )
  }

  async function leaveGroup(groupId) {
    await account.request(
      `/groups/${encodeURIComponent(groupId)}/members/me`,
      { method: 'DELETE' },
      () => {
        removeGroup(groupId)
      },
    )
  }

  async function kickMember(groupId, userId) {
    await account.request(
      `/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`,
      { method: 'DELETE' },
      () => {
        if (members.value[groupId]) {
          members.value[groupId] = members.value[groupId].filter(
            (member) => !sameId(member.user_id, userId),
          )
        }
      },
    )
  }

  async function changeRole(groupId, userId, role) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}/change-role`,
      {
        method: 'PATCH',
        body: { role },
      },
      (result) => {
        const member = members.value[groupId]?.find(
          (entry) => sameId(entry.user_id, userId),
        )

        if (member) {
          member.role = result?.role || role
        }

        return result
      },
    )
  }

  async function fetchMembers(groupId) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}/members`,
      undefined,
      (list) => {
        members.value[groupId] = Array.isArray(list) ? list : []

        return members.value[groupId]
      },
    )
  }

  async function requestAvatarUploadUrl(groupId, contentType) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}/avatar/upload-url`,
      {
        method: 'POST',
        body: { content_type: contentType },
      },
    )
  }

  async function setAvatar(groupId, key) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}/avatar`,
      {
        method: 'PUT',
        body: { key },
      },
      (group) => {
        upsertGroup(group)
        return group
      },
    )
  }

  async function deleteAvatar(groupId) {
    await account.request(
      `/groups/${encodeURIComponent(groupId)}/avatar`,
      { method: 'DELETE' },
      () => {
        const group = groups.value.find(
          (entry) => sameId(entry.group_id, groupId),
        )

        if (group) {
          group.avatar_url = null
          persist()
        }
      },
    )
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
      : hasSenderProfile(existing?.sender)
        ? existing.sender
        : findKnownSender(chat, message.sender_id)

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
    const ticket = account.ticket()
    account.assertCurrent(ticket)

    const requestKey = `${groupId}:${limit}:${offset}`
    const existingRequest = historyRequests.get(requestKey)

    if (existingRequest) return existingRequest

    const chat = ensureChat(groupId)
    chat.loading = true

    const request = (async () => {
      try {
        return await account.request(
          `/groups/${encodeURIComponent(groupId)}/messages?limit=${limit}&offset=${offset}`,
          undefined,
          (list) => {
            // Пользователь мог покинуть группу во время запроса.
            if (chats.value[groupId] !== chat) return chat

            const safeList = Array.isArray(list) ? list : []

            // Не теряем сообщения, пришедшие по WS.
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

            // Дополняем профили отправителей из REST.
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
          },
        )
      } finally {
        if (account.current(ticket)) {
          if (historyRequests.get(requestKey) === request) {
            historyRequests.delete(requestKey)
          }

          const prefix = `${groupId}:`

          chat.loading = [...historyRequests.keys()].some(
            (key) => key.startsWith(prefix),
          )
        }
      }
    })()

    historyRequests.set(requestKey, request)

    return request
  }

  function syncMissingSenders(groupId) {
    if (!account.active()) return Promise.resolve()

    const ticket = account.ticket()
    const key = String(groupId)

    pendingSenderSync.add(key)

    const existingRequest = senderSyncRequests.get(key)

    if (existingRequest) return existingRequest

    // Первый микротакт позволяет записать request в Map
    // до выполнения блока finally даже при раннем выходе.
    const request = Promise.resolve().then(async () => {
      try {
        while (
          account.current(ticket) &&
          pendingSenderSync.has(key)
        ) {
          pendingSenderSync.delete(key)

          const chat = chats.value[groupId]
          if (!chat) break

          const currentRequest = historyRequests.get(
            `${groupId}:30:0`,
          )

          if (currentRequest) {
            await currentRequest
          }

          account.assertCurrent(ticket)

          if (chats.value[groupId] !== chat) break

          await loadChat(groupId)
        }
      } catch (cause) {
        if (cause?.code !== 'SESSION_CHANGED') {
          console.error(
            'Не удалось загрузить отправителей сообщений группы:',
            cause,
          )
        }
      } finally {
        if (
          account.current(ticket) &&
          senderSyncRequests.get(key) === request
        ) {
          pendingSenderSync.delete(key)
          senderSyncRequests.delete(key)
        }
      }
    })

    senderSyncRequests.set(key, request)

    return request
  }

  async function sendMessage(groupId, content) {
    return await account.request(
      `/groups/${encodeURIComponent(groupId)}/messages`,
      {
        method: 'POST',
        body: { content },
      },
      (message) => {
        const chat = ensureChat(groupId)

        upsertMessage(chat, message)

        return message
      },
    )
  }

  function handleIncoming(payload) {
    if (!account.active()) return

    const groupId = payload.group_id
    if (groupId == null) return

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
