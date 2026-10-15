<script setup>
import UserAvatar from '@/components/UserAvatar.vue'

defineProps({
  user: { type: Object, required: true },
  showEmail: { type: Boolean, default: false },
  hideAvatar: { type: Boolean, default: false },
})
</script>

<template>
  <div class="user-card" :class="{ 'user-card--no-avatar': hideAvatar }">
    <UserAvatar v-if="!hideAvatar" :user="user" :size="88" />

    <div class="user-card-body">
      <div class="user-card-name">{{ user.name || user.username }}</div>
      <div class="user-card-username">@{{ user.username }}</div>

      <p v-if="user.bio" class="user-card-bio">{{ user.bio }}</p>

      <dl class="user-card-meta">
        <div v-if="user.city"><dt>Город</dt><dd>{{ user.city }}</dd></div>
        <div v-if="user.university"><dt>Университет</dt><dd>{{ user.university }}</dd></div>
        <div v-if="user.institute"><dt>Институт</dt><dd>{{ user.institute }}</dd></div>
        <div v-if="user.group"><dt>Группа</dt><dd>{{ user.group }}</dd></div>
        <div v-if="showEmail && user.email"><dt>Email</dt><dd>{{ user.email }}</dd></div>
      </dl>
    </div>
  </div>
</template>