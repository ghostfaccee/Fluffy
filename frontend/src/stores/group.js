import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'

const GROUPS_KEY = 'fluffy.groups'

function loadCachedGroups() {
  try {
    const raw = localStorage.getItem(GROUPS_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    return Array.isArray(arr) ? arr : []
  } catch {
    return []
  }
}

function saveCachedGroups(list) {
  try {
    localStorage.setItem(GROUPS_KEY, JSON.stringify(list))
  } catch {}
}

export const useGroupStore = defineStore('group', () => {
  const groups = ref(loadCachedGroups())
  const chats = ref({})
  const members = ref({})

  function persist() {
    saveCachedGroups(groups.value)
  }

  function upsertGroup(group) {
    let item = groups.value.find((g) => g.group_id === group.group_id)
    if (!item) {
      groups.value.unshift({ ...group })
    } else {
      Object.assign(item, group)
    }
    persist()
    return item
  }

  function removeGroup(groupId) {
    groups.value = groups.value.filter((g) => g.group_id !== groupId)
    persist()
    delete chats.value[groupId]
    delete members.value[groupId]
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
      body: { name, description: description || null },
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
    await api(`/groups/${encodeURIComponent(groupId)}`, { method: 'DELETE' })
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
    const group = await api(`/groups/${encodeURIComponent(groupId)}/invite-token`, {
      method: 'POST',
    })
    upsertGroup(group)
    return group
  }

  async function leaveGroup(groupId) {
    await api(`/groups/${encodeURIComponent(groupId)}/members/me`, { method: 'DELETE' })
    removeGroup(groupId)
  }

  async function kickMember(groupId, userId) {
    await api(`/groups/${encodeURIComponent(groupId)}/members/${encodeURIComponent(userId)}`, {
      method: 'DELETE',
    })
    if (members.value[groupId]) {
      members.value[groupId] = members.value[groupId].filter((m) => m.user_id !== userId)
    }
  }

  async function fetchMembers(groupId) {
    const list = await api(`/groups/${encodeURIComponent(groupId)}/members`)
    members.value[groupId] = Array.isArray(list) ? list : []
    return members.value[groupId]
  }

  async function requestAvatarUploadUrl(groupId, contentType) {
    return await api(`/groups/${encodeURIComponent(groupId)}/avatar/upload-url`, {
      method: 'POST',
      body: { content_type: contentType },
    })
  }

  async function setAvatar(groupId, key) {
    const group = await api(`/groups/${encodeURIComponent(groupId)}/avatar`, {
      method: 'PUT',
      body: { key },
    })
    upsertGroup(group)
    return group
  }

  async function deleteAvatar(groupId) {
    await api(`/groups/${encodeURIComponent(groupId)}/avatar`, { method: 'DELETE' })
    const group = groups.value.find((g) => g.group_id === groupId)
    if (group) {
      group.avatar_url = null
      persist()
    }
  }

  async function loadChat(groupId, { limit = 30, offset = 0 } = {}) {
    const chat = chats.value[groupId] || { messages: [], loading: false, hasMore: true }
    chat.loading = true
    chats.value[groupId] = chat
    try {
      const list = await api(
        `/groups/${encodeURIComponent(groupId)}/messages?limit=${limit}&offset=${offset}`
      )
      const messages = Array.isArray(list) ? [...list].reverse() : []
      if (offset === 0) chat.messages = messages
      else chat.messages = [...messages, ...chat.messages]
      chat.hasMore = list.length === limit
    } finally {
      chat.loading = false
    }
    return chat
  }

  async function sendMessage(groupId, content) {
    const msg = await api(`/groups/${encodeURIComponent(groupId)}/messages`, {
      method: 'POST',
      body: { content },
    })
    const chat = chats.value[groupId] || { messages: [], loading: false, hasMore: true }
    chat.messages.push(msg)
    chats.value[groupId] = chat
    return msg
  }

  function handleIncoming(payload) {
    const groupId = payload.group_id
    if (!groupId) return
    const chat = chats.value[groupId]
    if (!chat) return
    chat.messages.push({
      message_id: payload.message_id,
      group_id: groupId,
      sender_id: payload.sender_id,
      content: payload.content,
      created_at: payload.created_at,
      sender: null,
    })
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
    fetchMembers,
    requestAvatarUploadUrl,
    setAvatar,
    deleteAvatar,
    loadChat,
    sendMessage,
    handleIncoming,
  }
})