<script setup>
import GroupAvatar from '@/components/GroupAvatar.vue'

defineProps({
  group: { type: Object, required: true },
  role: { type: String, default: null },
})
</script>

<template>
  <div class="user-card">
    <GroupAvatar :group="group" :size="88" />
    <div class="user-card-body">
      <div class="user-card-name">{{ group.name }}</div>
      <p v-if="group.description" class="user-card-bio">{{ group.description }}</p>
      <dl class="user-card-meta">
        <div v-if="role"><dt>Роль</dt><dd>{{ role }}</dd></div>
      </dl>
    </div>
  </div>
</template>