<script setup>
import { computed } from 'vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'

const props = defineProps({
  user: { type: Object, required: true },
  showEmail: { type: Boolean, default: false },
  hideAvatar: { type: Boolean, default: false },
})

const details = computed(() => [
  { label: 'Город', value: props.user.city },
  { label: 'Университет', value: props.user.university },
  { label: 'Институт', value: props.user.institute },
  { label: 'Группа', value: props.user.group },
  { label: 'Email', value: props.showEmail ? props.user.email : null },
].filter((item) => item.value))
</script>

<template>
  <article class="profile-summary" :class="{ 'profile-summary--flat': hideAvatar }">
    <UserAvatar v-if="!hideAvatar" :user="user" :size="72" />

    <div class="profile-summary__body">
      <header>
        <h2>{{ user.name || user.username }}</h2>
        <span class="profile-summary__username">@{{ user.username }}</span>
      </header>

      <p v-if="user.bio" class="profile-summary__bio">{{ user.bio }}</p>

      <dl v-if="details.length" class="profile-summary__details">
        <div v-for="item in details" :key="item.label">
          <dt>{{ item.label }}</dt>
          <dd>{{ item.value }}</dd>
        </div>
      </dl>
    </div>
  </article>
</template>

<style scoped>
.profile-summary {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  align-items: start;
  gap: 18px;
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-card);
}

.profile-summary--flat {
  grid-template-columns: minmax(0, 1fr);
}

.profile-summary__body {
  min-width: 0;
}

.profile-summary h2 {
  margin: 0;
  color: var(--text);
  font-size: 21px;
  font-weight: 650;
  line-height: 1.3;
  letter-spacing: -0.5px;
  overflow-wrap: anywhere;
}

.profile-summary__username {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.profile-summary__bio {
  margin: 14px 0 0;
  color: var(--text);
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.profile-summary__details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 180px), 1fr));
  gap: 16px 24px;
  margin: 18px 0 0;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.profile-summary__details > div {
  min-width: 0;
}

.profile-summary__details dt {
  margin: 0 0 5px;
  color: var(--muted);
  font-size: 12px;
}

.profile-summary__details dd {
  margin: 0;
  color: var(--text);
  font-size: 13px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

@media (max-width: 480px) {
  .profile-summary {
    gap: 12px;
    padding: 16px;
  }

  .profile-summary h2 {
    font-size: 19px;
  }
}
</style>
