<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppIcon from '@/shared/ui/AppIcon.vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import { fetchUserById } from '@/shared/api/users'
import { friendshipErrorMessage, friendshipsApi } from '@/modules/friendships/api/friendships'

const props = defineProps({
  kind: { type: String, required: true },
  currentUserId: { type: String, required: true },
  profileUserId: { type: String, default: null },
  monitor: Boolean,
})
const emit = defineEmits(['count-change'])

const copy = {
  incoming: { title: 'Входящие заявки', empty: 'Входящих заявок пока нет.', remove: 'Отклонить' },
  outgoing: { title: 'Исходящие заявки', empty: 'Исходящих заявок пока нет.', remove: 'Отменить' },
  accepted: { title: 'Друзья', empty: 'Друзей пока нет.', remove: 'Удалить из друзей' },
}

const rows = ref([])
const loaded = ref(false)
const loading = ref(false)
const loadError = ref('')
const expanded = ref(false)
let active = true
let revision = 0
let timer

async function loadUser(row) {
  row.userRequested = true
  row.userLoading = true
  try {
    row.user = await fetchUserById(row.userId)
  } catch {
    row.user = null
  } finally {
    row.userLoading = false
  }
}

function loadVisibleUsers() {
  if (!expanded.value) return
  rows.value.filter((row) => !row.userRequested).forEach(loadUser)
}

async function load() {
  if (loading.value) return

  loading.value = true
  loadError.value = ''
  const startedAt = revision

  try {
    const friendships = await friendshipsApi.list(props.kind, props.profileUserId)
    if (!active || startedAt !== revision) return

    const ownerId = props.profileUserId ?? props.currentUserId
    const previousRows = new Map(rows.value.map((row) => [row.userId, row]))
    rows.value = friendships.map(({ user_low_id, user_high_id }) => {
      const userId = user_low_id === ownerId ? user_high_id : user_low_id
      return previousRows.get(userId) ?? {
        userId, user: null, userRequested: false, userLoading: false, busy: false, error: '',
      }
    })
    loaded.value = true
    loadVisibleUsers()
  } catch (error) {
    if (!loaded.value) loadError.value = friendshipErrorMessage(error, 'Не удалось загрузить список.')
  } finally {
    loading.value = false
  }
}

function onToggle(event) {
  expanded.value = event.currentTarget.open
  if (!expanded.value) return
  if (loaded.value) loadVisibleUsers()
  else load()
}

async function resolveRequest(row, action) {
  if (row.busy || props.profileUserId) return
  if (props.kind === 'accepted' && !window.confirm('Удалить пользователя из друзей?')) return

  row.busy = true
  row.error = ''

  try {
    await action(row.userId)
    revision += 1
    rows.value = rows.value.filter(({ userId }) => userId !== row.userId)
  } catch (error) {
    const fallback = props.kind === 'accepted'
      ? 'Не удалось удалить пользователя из друзей.'
      : 'Не удалось обновить заявку.'
    row.error = friendshipErrorMessage(error, fallback)
  } finally {
    row.busy = false
  }
}

watch(() => rows.value.length, (count) => emit('count-change', count))

onMounted(() => {
  if (props.monitor || props.kind === 'accepted') load()
  if (props.monitor) {
    timer = window.setInterval(() => {
      if (document.visibilityState === 'visible') load()
    }, 30_000)
  }
})

onBeforeUnmount(() => {
  active = false
  window.clearInterval(timer)
})
</script>

<template>
  <details class="friendship-list" :class="{ 'friendship-list--compact': kind === 'accepted' }" @toggle="onToggle">
    <summary
      class="friendship-list__summary"
      :aria-label="kind === 'accepted' ? `${copy[kind].title}${loaded ? `: ${rows.length}` : ''}` : undefined"
      :title="kind === 'accepted' ? copy[kind].title : undefined"
    >
      <AppIcon name="groups" :size="20" class="friendship-list__icon" />
      <span v-if="kind !== 'accepted'" class="friendship-list__title">{{ copy[kind].title }}</span>
      <span v-if="loaded || kind === 'accepted'" class="friendship-list__count">{{ loaded ? rows.length : '–' }}</span>
      <AppIcon v-if="kind !== 'accepted'" name="arrow" :size="16" class="friendship-list__arrow" />
    </summary>

    <div class="friendship-list__body">
      <p v-if="!loaded && !loadError" class="friendship-list__message" role="status">
        Загружаем…
      </p>
      <div v-else-if="loadError" class="friendship-list__message">
        <p class="form-error" role="alert">{{ loadError }}</p>
        <button class="btn btn-secondary btn-small" type="button" @click="load">
          Повторить
        </button>
      </div>
      <p v-else-if="!rows.length" class="friendship-list__message">{{ copy[kind].empty }}</p>

      <table v-else class="friendship-list__table" :aria-label="copy[kind].title">
        <tbody>
          <tr v-for="row in rows" :key="row.userId">
            <td>
              <div class="friendship-list__row">
                <RouterLink
                  v-if="row.user"
                  :to="{ name: 'user', params: { username: row.user.username } }"
                  class="friendship-list__user"
                >
                  <UserAvatar :user="row.user" :size="36" />
                  <span>
                    <strong>{{ row.user.name || `@${row.user.username}` }}</strong>
                    <small v-if="row.user.name">@{{ row.user.username }}</small>
                  </span>
                </RouterLink>
                <div v-else class="friendship-list__user">
                  <UserAvatar :user="{}" :size="36" />
                  <span v-if="row.userLoading">Загружаем профиль…</span>
                  <span v-else>Профиль недоступен</span>
                </div>

                <div v-if="!profileUserId" class="friendship-list__actions">
                  <button
                    v-if="kind === 'incoming'"
                    class="btn btn-primary btn-small"
                    type="button"
                    :disabled="row.busy"
                    @click="resolveRequest(row, friendshipsApi.accept)"
                  >
                    Принять
                  </button>
                  <button
                    class="btn btn-secondary btn-small"
                    type="button"
                    :disabled="row.busy"
                    @click="resolveRequest(row, friendshipsApi.remove)"
                  >
                    {{ copy[kind].remove }}
                  </button>
                </div>
              </div>
              <p v-if="row.error" class="form-error" role="alert">{{ row.error }}</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </details>
</template>

<style scoped>
.friendship-list {
  width: 100%;
  min-width: 0;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: transparent;
}

.friendship-list__summary {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: inherit;
  color: var(--text);
  list-style: none;
  cursor: pointer;
}

.friendship-list__summary::-webkit-details-marker {
  display: none;
}

.friendship-list__summary:hover {
  background: var(--bg-soft);
}

.friendship-list__summary:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.friendship-list__icon {
  flex: none;
  color: var(--muted);
}

.friendship-list--compact:not([open]) {
  width: fit-content;
}

.friendship-list--compact .friendship-list__summary {
  justify-content: center;
  min-height: 36px;
  padding: 5px 10px;
}

.friendship-list--compact[open] .friendship-list__summary {
  background: var(--bg-soft);
}

.friendship-list__title {
  flex: 1;
  font-size: 14px;
  font-weight: 650;
  overflow-wrap: anywhere;
}

.friendship-list__count,
.friendship-list__arrow {
  flex: none;
  color: var(--muted);
}

.friendship-list__count {
  padding: 2px 7px;
  border-radius: 999px;
  background: var(--bg-soft);
  font-size: 12px;
  font-variant-numeric: tabular-nums;
}

.friendship-list[open] .friendship-list__arrow {
  transform: rotate(90deg);
}

.friendship-list__body {
  border-top: 1px solid var(--border);
}

.friendship-list__message {
  margin: 0;
  padding: 14px;
  color: var(--muted);
  font-size: 13px;
}

.friendship-list__table {
  width: 100%;
  table-layout: fixed;
  border-collapse: collapse;
}

.friendship-list__table td {
  padding: 12px 14px;
}

.friendship-list__table tr + tr td {
  border-top: 1px solid var(--border);
}

.friendship-list__row,
.friendship-list__actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.friendship-list__row {
  justify-content: space-between;
}

.friendship-list__user {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  color: var(--text);
  font-size: 13px;
  text-decoration: none;
  overflow-wrap: anywhere;
}

a.friendship-list__user:hover strong {
  text-decoration: underline;
}

.friendship-list__user strong,
.friendship-list__user small {
  display: block;
}

.friendship-list__user small {
  color: var(--muted);
}
</style>
