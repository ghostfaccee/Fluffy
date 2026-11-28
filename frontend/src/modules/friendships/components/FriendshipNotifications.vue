<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AppIcon from '@/shared/ui/AppIcon.vue'
import FriendshipList from '@/modules/friendships/components/FriendshipList.vue'

defineProps({ currentUserId: { type: String, required: true } })

const route = useRoute()
const root = ref(null)
const trigger = ref(null)
const open = ref(false)
const incomingCount = ref(0)

function onOutsideClick(event) {
  if (!root.value?.contains(event.target)) open.value = false
}

function onEscape(event) {
  if (event.key !== 'Escape' || !open.value) return
  open.value = false
  if (root.value?.contains(document.activeElement)) trigger.value?.focus()
}

watch(() => route.fullPath, () => { open.value = false })

onMounted(() => {
  document.addEventListener('pointerdown', onOutsideClick)
  document.addEventListener('keydown', onEscape)
})

onUnmounted(() => {
  document.removeEventListener('pointerdown', onOutsideClick)
  document.removeEventListener('keydown', onEscape)
})
</script>

<template>
  <div ref="root" class="friendship-notifications">
    <button
      ref="trigger"
      class="friendship-notifications__trigger"
      type="button"
      :aria-label="incomingCount ? `Заявки в друзья. Входящие: ${incomingCount}` : 'Заявки в друзья'"
      :aria-expanded="open"
      aria-controls="friendship-notifications"
      title="Заявки в друзья"
      @click="open = !open"
    >
      <AppIcon name="bell" :size="20" />
      <span v-if="incomingCount" class="friendship-notifications__dot" aria-hidden="true" />
    </button>

    <section
      v-show="open"
      id="friendship-notifications"
      class="friendship-notifications__panel"
      aria-labelledby="friendship-notifications-title"
    >
      <h2 id="friendship-notifications-title">Заявки в друзья</h2>
      <FriendshipList
        kind="incoming"
        :current-user-id="currentUserId"
        monitor
        @count-change="incomingCount = $event"
      />
      <FriendshipList kind="outgoing" :current-user-id="currentUserId" />
    </section>
  </div>
</template>

<style scoped>
.friendship-notifications {
  position: relative;
  flex: none;
}

.friendship-notifications__trigger {
  position: relative;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  padding: 0;
  border: 0;
  border-radius: 10px;
  background: transparent;
  color: var(--muted);
  cursor: pointer;
}

.friendship-notifications__trigger:hover,
.friendship-notifications__trigger[aria-expanded='true'] {
  background: var(--bg-soft);
  color: var(--text);
}

.friendship-notifications__dot {
  position: absolute;
  top: 7px;
  right: 7px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 0 0 2px var(--bg-card);
}

.friendship-notifications__panel {
  position: absolute;
  top: calc(100% + 12px);
  right: 0;
  display: grid;
  gap: 8px;
  width: min(420px, calc(100vw - 72px));
  max-height: calc(100dvh - 150px);
  padding: 12px;
  overflow: auto;
  overscroll-behavior: contain;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-card);
  box-shadow: 0 12px 32px rgb(0 0 0 / 16%);
}

.friendship-notifications__panel h2 {
  margin: 2px 4px 4px;
  font-size: 15px;
  font-weight: 650;
}

@media (max-width: 700px) {
  .friendship-notifications__panel {
    position: fixed;
    inset: 66px 14px auto;
    width: auto;
    max-width: 420px;
    margin-left: auto;
  }
}
</style>
