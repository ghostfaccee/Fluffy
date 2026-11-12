<script setup>
import ModuleGroupCard from '@/modules/groups/components/GroupCard.vue'

defineProps({
  group: { type: Object, required: true },
  role: { type: String, default: null },
})
</script>

<template>
  <ModuleGroupCard
    :group="group"
    :role="role"
  />
</template>
