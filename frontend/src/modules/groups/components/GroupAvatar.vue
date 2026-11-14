<script setup>
import { computed } from 'vue'

const props = defineProps({
  group: {
    type: Object,
    required: true,
  },
  size: {
    type: Number,
    default: 64,
  },
})

const initials = computed(() => {
  const name = String(props.group.name || '').trim()

  if (!name) {
    return '?'
  }

  const parts = name.split(/\s+/)

  if (parts.length === 1) {
    return parts[0].slice(0, 2).toUpperCase()
  }

  return (parts[0].charAt(0) + parts[1].charAt(0)).toUpperCase()
})

const avatarStyle = computed(() => ({
  width: `${props.size}px`,
  height: `${props.size}px`,
  fontSize: `${Math.round(props.size * 0.38)}px`,
}))
</script>

<template>
  <img
    v-if="group.avatar_url"
    :src="group.avatar_url"
    :alt="group.name || ''"
    class="group-avatar group-avatar--img"
    :style="avatarStyle"
  />
  <div
    v-else
    class="group-avatar group-avatar--initials"
    :style="avatarStyle"
    aria-hidden="true"
  >
    {{ initials }}
  </div>
</template>
