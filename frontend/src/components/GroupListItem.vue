<script setup>
import GroupAvatar from '@/components/GroupAvatar.vue'

defineProps({
  group: { type: Object, required: true },
  active: { type: Boolean, default: false },
})
</script>

<template>
  <RouterLink
    :to="{ name: 'group', params: { groupId: group.group_id } }"
    class="chat-list-item"
    :class="{ active }"
  >
    <GroupAvatar :group="group" :size="44" />
    <div class="chat-list-body">
      <div class="chat-list-top">
        <span class="chat-list-name">{{ group.name }}</span>
      </div>
      <div class="chat-list-preview">
        {{ group.description || 'Группа' }}
      </div>
    </div>
  </RouterLink>
</template>