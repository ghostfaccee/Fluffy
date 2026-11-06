<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import UserAvatar from '@/components/UserAvatar.vue'
import DoubleCheckIcon from '@/components/DoubleCheckIcon.vue'

const props = defineProps({
  message: { type: Object, required: true },
})

const auth = useAuthStore()
const mine = computed(() => props.message.sender_id === auth.user?.user_id)

function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="msg-row" :class="{ 'msg-row--mine': mine }">
    <UserAvatar
      v-if="!mine && message.sender"
      :user="message.sender"
      :size="32"
    />
    <div class="msg-bubble" :class="{ 'msg-bubble--mine': mine }">
      <div class="msg-content">{{ message.content }}</div>
      <div class="msg-meta">
        <span class="msg-time">{{ formatTime(message.created_at) }}</span>
        <span
          v-if="mine"
          class="msg-status"
          :class="{ 'msg-status--read': message.is_read }"
          :title="message.is_read ? 'Прочитано' : 'Отправлено'"
        >
          <DoubleCheckIcon />
        </span>
      </div>
    </div>
  </div>
</template>