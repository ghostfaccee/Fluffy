<script setup>
import ModuleGroupAvatar from '@/modules/groups/components/GroupAvatar.vue'

defineProps({
  group: {
    type: Object,
    required: true,
  },
  size: {
    type: Number,
    default: 64,
  },
})
</script>

<template>
  <ModuleGroupAvatar
    :group="group"
    :size="size"
  />
</template>
