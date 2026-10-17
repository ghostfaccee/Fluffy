<script setup>
import { computed } from 'vue'

const props = defineProps({
  group: { type: Object, required: true },
  size: { type: Number, default: 64 },
})

const initials = computed(() => {
  const src = (props.group?.name || '?').trim()
  const parts = src.split(/\s+/)
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase()
  return (parts[0][0] + parts[1][0]).toUpperCase()
})

const style = computed(() => ({
  width: props.size + 'px',
  height: props.size + 'px',
  fontSize: Math.round(props.size * 0.38) + 'px',
}))
</script>

<template>
  <img
    v-if="group?.avatar_url"
    :src="group.avatar_url"
    :alt="group.name"
    class="group-avatar group-avatar--img"
    :style="style"
  />
  <div v-else class="group-avatar group-avatar--initials" :style="style" aria-hidden="true">
    {{ initials }}
  </div>
</template>