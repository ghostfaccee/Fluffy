<script setup>
import { computed } from 'vue'

const props = defineProps({
  user: { type: Object, required: true },
  size: { type: Number, default: 64 },
})

const initials = computed(() => {
  const src = props.user?.name || props.user?.username || '?'
  const parts = src.trim().split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
})

const style = computed(() => ({
  width: props.size + 'px',
  height: props.size + 'px',
  fontSize: Math.round(props.size * 0.4) + 'px',
}))
</script>

<template>
  <img
    v-if="user?.avatar_url"
    :src="user.avatar_url"
    :alt="user.username"
    class="user-avatar user-avatar--img"
    :style="style"
  />
  <div v-else class="user-avatar user-avatar--initials" :style="style" aria-hidden="true">
    {{ initials }}
  </div>
</template>