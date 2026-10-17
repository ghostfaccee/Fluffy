<script setup>
import UserAvatar from '@/components/UserAvatar.vue'

defineProps({
  conversation: { type: Object, required: true },
  active: { type: Boolean, default: false },
})

function preview(text) {
  if (!text) return 'Нет сообщений'
  return text.length > 40 ? text.slice(0, 40) + '…' : text
}
</script>

<template>
  <RouterLink
    :to="{ name: 'chat', params: { userId: conversation.user_id } }"
    class="chat-list-item"
    :class="{ active }"
  >
    <UserAvatar
      :user="{
        username: conversation.username || conversation.user_id,
        name: conversation.name,
        avatar_url: conversation.avatar_url,
      }"
      :size="44"
    />
    <div class="chat-list-body">
      <div class="chat-list-top">
        <span class="chat-list-name">
          {{ conversation.name || conversation.username || 'Пользователь' }}
        </span>
      </div>
      <div class="chat-list-preview">{{ preview(conversation.lastMessage) }}</div>
    </div>
    <span v-if="conversation.unread" class="chat-list-badge">{{ conversation.unread }}</span>
  </RouterLink>
</template>
