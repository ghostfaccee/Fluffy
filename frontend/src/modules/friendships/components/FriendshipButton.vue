<script setup>
import { computed, onMounted, ref } from 'vue'
import AppIcon from '@/shared/ui/AppIcon.vue'
import { friendshipErrorMessage, friendshipsApi } from '@/modules/friendships/api/friendships'

const props = defineProps({
  currentUserId: { type: String, required: true },
  userId: { type: String, required: true },
})

const friendship = ref(null)
const loading = ref(true)
const saving = ref(false)
const loadError = ref('')
const actionError = ref('')

const incoming = computed(() =>
  friendship.value?.status === 'pending' &&
  friendship.value.requested_by !== props.currentUserId,
)

async function load() {
  loading.value = true
  loadError.value = ''

  try {
    friendship.value = await friendshipsApi.get(props.userId)
  } catch (error) {
    loadError.value = friendshipErrorMessage(error, 'Не удалось проверить статус дружбы.')
  } finally {
    loading.value = false
  }
}

async function submit() {
  if (saving.value) return

  saving.value = true
  actionError.value = ''
  const action = incoming.value ? friendshipsApi.accept : friendshipsApi.create

  try {
    friendship.value = await action(props.userId)
  } catch (error) {
    actionError.value = friendshipErrorMessage(error, 'Не удалось обновить заявку.')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="friendship-status">
    <span v-if="loading" class="friendship-status__badge" role="status">
      <AppIcon name="clock" :size="16" />
      Проверяем…
    </span>
    <template v-else-if="loadError">
      <p class="form-error" role="alert">{{ loadError }}</p>
      <button class="btn btn-secondary btn-small" type="button" @click="load">
        Повторить
      </button>
    </template>
    <button
      v-else-if="!friendship || incoming"
      class="btn btn-secondary"
      type="button"
      :disabled="saving"
      @click="submit"
    >
      {{ incoming ? 'Принять заявку' : 'Добавить в друзья' }}
    </button>
    <span
      v-else
      class="friendship-status__badge"
      :class="{ 'friendship-status__badge--accepted': friendship.status === 'accepted' }"
      role="status"
    >
      <AppIcon :name="friendship.status === 'accepted' ? 'check' : 'clock'" :size="16" />
      {{ friendship.status === 'accepted' ? 'В друзьях' : 'Заявка отправлена' }}
    </span>

    <p v-if="actionError" class="form-error" role="alert">{{ actionError }}</p>
  </div>
</template>

<style scoped>
.friendship-status {
  align-self: center;
}

.friendship-status__badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 4px 10px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--bg-soft);
  color: var(--muted);
  font-size: 12px;
  font-weight: 600;
}

.friendship-status__badge--accepted {
  color: var(--text);
}

.friendship-status__badge--accepted svg {
  color: var(--accent);
}
</style>
