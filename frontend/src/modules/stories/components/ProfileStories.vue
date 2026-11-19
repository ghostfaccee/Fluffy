<script setup>
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue'
import { useAuthStore } from '@/modules/auth/stores/auth'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import StoryComposer from '@/modules/stories/components/StoryComposer.vue'
import StoryViewer from '@/modules/stories/components/StoryViewer.vue'
import {
  STORY_LIMIT,
  getStoryArchive,
  getUserStories,
  isStoryActive,
  isVideoStory,
  sortStories,
  storyErrorMessage,
} from '@/modules/stories/api/stories'

const props = defineProps({
  user: {
    type: Object,
    required: true,
  },
  size: {
    type: Number,
    default: 128,
  },
})

const auth = useAuthStore()

const activeStories = ref([])
const archiveStories = ref([])
const loading = ref(false)
const archiveLoading = ref(false)
const error = ref('')
const archiveError = ref('')
const composerOpen = ref(false)
const archiveOpen = ref(false)
const archiveDialog = ref(null)
const viewer = ref(null)
const now = ref(Date.now())

let disposed = false
let activeGeneration = 0
let archiveGeneration = 0
let expirationTimer = null

const own = computed(
  () =>
    Boolean(auth.user?.user_id) &&
    String(auth.user.user_id) === String(props.user.user_id),
)

const active = computed(() =>
  sortStories(
    activeStories.value.filter((story) => isStoryActive(story, now.value)),
  ),
)

// Архив отображает весь ответ сервера, включая активные истории.
// Новые истории находятся в начале списка.
const archiveItems = computed(() =>
  sortStories(archiveStories.value).reverse(),
)

const hasStories = computed(() => active.value.length > 0)

const canCreate = computed(
  () => own.value && !loading.value && active.value.length < STORY_LIMIT,
)

const avatarLabel = computed(() => {
  const name = props.user.name || props.user.username

  return hasStories.value
    ? `Открыть истории пользователя ${name}. Активных: ${active.value.length}`
    : `Аватар пользователя ${name}. Активных историй нет`
})

const createLabel = computed(() => {
  if (loading.value) return 'Загружаем список историй'

  if (active.value.length >= STORY_LIMIT) {
    return `Достигнут лимит: ${STORY_LIMIT} активных историй`
  }

  return 'Создать историю'
})

function scheduleExpiration() {
  window.clearTimeout(expirationTimer)
  now.value = Date.now()

  const nextExpiration = [
    ...activeStories.value,
    ...archiveStories.value,
  ]
    .map((story) => Date.parse(story.expires_at))
    .filter((expiresAt) => Number.isFinite(expiresAt) && expiresAt > now.value)
    .sort((first, second) => first - second)[0]

  if (!nextExpiration) return

  expirationTimer = window.setTimeout(
    scheduleExpiration,
    Math.min(nextExpiration - now.value + 50, 2_147_483_647),
  )
}

async function loadActive() {
  const username = props.user.username
  const accountId = auth.user?.user_id

  if (!username || !accountId) return

  const requestGeneration = ++activeGeneration

  loading.value = true
  error.value = ''

  try {
    const stories = await getUserStories(username)

    if (
      disposed ||
      requestGeneration !== activeGeneration ||
      String(auth.user?.user_id) !== String(accountId)
    ) {
      return
    }

    activeStories.value = stories
    scheduleExpiration()
  } catch (cause) {
    if (!disposed && requestGeneration === activeGeneration) {
      error.value = storyErrorMessage(cause)
    }
  } finally {
    if (!disposed && requestGeneration === activeGeneration) {
      loading.value = false
    }
  }
}

async function loadArchive() {
  if (!own.value) return

  const accountId = auth.user?.user_id
  const requestGeneration = ++archiveGeneration

  archiveLoading.value = true
  archiveError.value = ''

  try {
    const stories = await getStoryArchive()

    if (
      disposed ||
      requestGeneration !== archiveGeneration ||
      !own.value ||
      String(auth.user?.user_id) !== String(accountId)
    ) {
      return
    }

    archiveStories.value = stories

    // Архивный endpoint возвращает все истории владельца.
    // Из этого же ответа актуализируем активные истории аватарки.
    activeStories.value = stories.filter((story) => isStoryActive(story))

    scheduleExpiration()
  } catch (cause) {
    if (!disposed && requestGeneration === archiveGeneration) {
      archiveError.value = storyErrorMessage(cause)
    }
  } finally {
    if (!disposed && requestGeneration === archiveGeneration) {
      archiveLoading.value = false
    }
  }
}

function openActive() {
  now.value = Date.now()

  if (!active.value.length) return

  viewer.value = {
    stories: [...active.value],
    initialIndex: 0,
    archive: false,
  }
}

function openComposer() {
  now.value = Date.now()

  if (!canCreate.value) return

  composerOpen.value = true
}

function closeArchive() {
  archiveOpen.value = false
}

function openArchive() {
  if (!own.value) return

  archiveOpen.value = true
  loadArchive()
}

function openArchivedStory(index) {
  const stories = [...archiveItems.value]

  if (!stories[index]) return

  // Закрываем архив перед открытием просмотрщика:
  // одновременно остаётся только одно модальное окно.
  closeArchive()

  viewer.value = {
    stories,
    initialIndex: index,
    archive: true,
  }
}

function closeViewer() {
  const returnToArchive = viewer.value?.archive && own.value

  viewer.value = null

  if (returnToArchive) {
    archiveOpen.value = true
  }
}

function onCreated(story) {
  composerOpen.value = false
  error.value = ''

  // Старые ответы GET не должны затереть только что созданную историю.
  activeGeneration += 1
  archiveGeneration += 1
  loading.value = false
  archiveLoading.value = false

  activeStories.value = [
    ...activeStories.value.filter((item) => item.story_id !== story.story_id),
    story,
  ]

  archiveStories.value = [
    ...archiveStories.value.filter((item) => item.story_id !== story.story_id),
    story,
  ]

  scheduleExpiration()
}

function onDeleted(storyId) {
  // Не допускаем восстановления удалённой истории
  // из ответа запроса, начатого до удаления.
  activeGeneration += 1
  archiveGeneration += 1
  loading.value = false
  archiveLoading.value = false

  activeStories.value = activeStories.value.filter(
    (story) => story.story_id !== storyId,
  )

  archiveStories.value = archiveStories.value.filter(
    (story) => story.story_id !== storyId,
  )

  closeViewer()
  scheduleExpiration()
}

function onVisibilityChange() {
  if (document.hidden) return

  scheduleExpiration()

  if (
    !viewer.value &&
    !composerOpen.value &&
    !archiveOpen.value &&
    !loading.value
  ) {
    loadActive()
  }
}

function formatDate(value) {
  const date = new Date(value)

  if (!Number.isFinite(date.getTime())) return ''

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

watch(
  archiveOpen,
  (open) => {
    const dialog = archiveDialog.value

    if (!dialog) return

    if (open && !dialog.open) {
      dialog.showModal()
    } else if (!open && dialog.open) {
      dialog.close()
    }
  },
  { flush: 'post' },
)

watch(
  [
    () => props.user.user_id,
    () => props.user.username,
    () => auth.user?.user_id,
  ],
  () => {
    activeGeneration += 1
    archiveGeneration += 1
    window.clearTimeout(expirationTimer)

    activeStories.value = []
    archiveStories.value = []
    loading.value = false
    archiveLoading.value = false
    error.value = ''
    archiveError.value = ''
    composerOpen.value = false
    archiveOpen.value = false
    viewer.value = null
    now.value = Date.now()

    loadActive()
  },
  { immediate: true },
)

onMounted(() => {
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  disposed = true
  activeGeneration += 1
  archiveGeneration += 1

  window.clearTimeout(expirationTimer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  archiveDialog.value?.close()
})
</script>

<template>
  <div class="profile-stories">
    <div class="profile-stories__avatar-wrapper">
      <button
        class="profile-stories__avatar"
        :class="{ 'profile-stories__avatar--active': hasStories }"
        type="button"
        :disabled="!hasStories"
        :aria-label="avatarLabel"
        :title="hasStories ? 'Посмотреть истории' : 'Нет активных историй'"
        @click="openActive"
      >
        <UserAvatar :user="user" :size="size" />
      </button>

      <button
        v-if="own"
        class="profile-stories__create"
        type="button"
        :disabled="!canCreate"
        :aria-label="createLabel"
        :title="createLabel"
        @click="openComposer"
      >
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
          focusable="false"
        >
          <path
            d="M12 5v14M5 12h14"
            stroke="currentColor"
            stroke-width="2.5"
            stroke-linecap="round"
          />
        </svg>
      </button>
    </div>

    <div
      v-if="own"
      class="profile-stories__actions"
      aria-label="Управление историями"
    >
      <button
        class="profile-stories__action"
        type="button"
        :disabled="loading"
        @click="loadActive"
      >
        <svg
          class="profile-stories__action-icon"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
          focusable="false"
        >
          <path
            d="M20 7v5h-5M4 17v-5h5"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
          <path
            d="M6.1 7a7 7 0 0 1 11.55-1.6L20 8M4 16l2.35 2.6A7 7 0 0 0 17.9 17"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>

        <span>{{ loading ? 'Загрузка…' : 'Обновить' }}</span>
      </button>

      <button
        class="profile-stories__action"
        type="button"
        @click="openArchive"
      >
        <svg
          class="profile-stories__action-icon"
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          aria-hidden="true"
          focusable="false"
        >
          <path
            d="M4 9h16v11H4V9ZM3 4h18v5H3V4ZM9 13h6"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>

        <span>Архив</span>
      </button>
    </div>

    <p v-if="error" class="profile-stories__error" role="alert">
      {{ error }}

      <button
        v-if="!own"
        class="profile-stories__retry"
        type="button"
        :disabled="loading"
        @click="loadActive"
      >
        Повторить
      </button>
    </p>

    <dialog
      v-if="own"
      ref="archiveDialog"
      class="stories-archive"
      aria-labelledby="stories-archive-title"
      @cancel.prevent="closeArchive"
    >
      <div class="stories-archive__content">
        <header class="stories-archive__header">
          <div>
            <h2 id="stories-archive-title">Архив историй</h2>
            <p>Все ваши истории, включая активные.</p>
          </div>

          <button
            class="btn btn-secondary btn-small"
            type="button"
            @click="closeArchive"
          >
            Закрыть
          </button>
        </header>

        <p v-if="archiveLoading" class="stories-archive__status" role="status">
          Загружаем архив…
        </p>

        <div v-else-if="archiveError" role="alert">
          <p class="form-error">{{ archiveError }}</p>

          <button
            class="btn btn-secondary btn-small"
            type="button"
            @click="loadArchive"
          >
            Повторить
          </button>
        </div>

        <p v-else-if="!archiveItems.length" class="stories-archive__status">
          Вы пока не публиковали истории.
        </p>

        <div v-else class="stories-archive__list">
          <button
            v-for="(story, index) in archiveItems"
            :key="story.story_id"
            class="stories-archive__item"
            type="button"
            :aria-label="`Открыть историю: ${story.title}`"
            @click="openArchivedStory(index)"
          >
            <span class="stories-archive__meta">
              <span class="stories-archive__kind">
                {{ isVideoStory(story) ? 'Видео' : 'Фото' }}
              </span>

              <span
                v-if="isStoryActive(story, now)"
                class="stories-archive__badge"
              >
                Активна
              </span>
            </span>

            <span class="stories-archive__title">
              {{ story.title }}
            </span>

            <time
              class="stories-archive__date"
              :datetime="story.created_at"
            >
              {{ formatDate(story.created_at) }}
            </time>
          </button>
        </div>
      </div>
    </dialog>

    <StoryComposer
      v-if="composerOpen && own"
      @close="composerOpen = false"
      @created="onCreated"
    />

    <StoryViewer
      v-if="viewer"
      :stories="viewer.stories"
      :initial-index="viewer.initialIndex"
      :archive="viewer.archive"
      :own="own"
      @close="closeViewer"
      @deleted="onDeleted"
    />
  </div>
</template>

<style scoped>
.profile-stories {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  width: 100%;
  min-width: 0;
}

.profile-stories__avatar-wrapper {
  position: relative;
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
}

.profile-stories__avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px;
  color: inherit;
  background: transparent;
  border: 3px solid transparent;
  border-radius: 50%;
  cursor: default;
}

.profile-stories__avatar--active {
  border-color: var(--accent);
  cursor: pointer;
}

.profile-stories__avatar--active:hover {
  opacity: 0.85;
}

.profile-stories__avatar:disabled {
  opacity: 1;
}

.profile-stories__create {
  position: absolute;
  right: 4px;
  bottom: 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  padding: 0;
  color: #fff;
  background: var(--accent);
  border: 3px solid var(--bg);
  border-radius: 50%;
  box-shadow: 0 2px 8px rgb(0 0 0 / 14%);
  cursor: pointer;
  transition: transform 150ms ease, opacity 150ms ease;
}

.profile-stories__create:hover:not(:disabled) {
  transform: scale(1.08);
}

.profile-stories__create:disabled {
  opacity: 0.5;
  cursor: default;
}

.profile-stories__avatar:focus-visible,
.profile-stories__create:focus-visible,
.profile-stories__action:focus-visible,
.stories-archive__item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
}

.profile-stories__actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  width: 100%;
}

.profile-stories__action {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  min-width: 0;
  padding: 10px 6px;
  color: var(--text);
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  line-height: 1.4;
  text-align: center;
  background: var(--bg-card, transparent);
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  transition: border-color 150ms ease;
}

.profile-stories__action:hover:not(:disabled) {
  border-color: var(--accent);
}

.profile-stories__action:disabled {
  opacity: 0.5;
  cursor: default;
}

.profile-stories__action-icon {
  flex-shrink: 0;
  color: var(--muted);
}

.profile-stories__error {
  width: 100%;
  margin: 0;
  color: #e57373;
  font-size: 12px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.profile-stories__retry {
  display: block;
  margin-top: 6px;
  padding: 0;
  color: var(--text);
  font: inherit;
  text-decoration: underline;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.stories-archive {
  width: min(620px, calc(100vw - 32px));
  max-height: calc(100dvh - 32px);
  margin: auto;
  padding: 0;
  overflow: auto;
  color: var(--text);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
}

.stories-archive::backdrop {
  background: rgb(0 0 0 / 72%);
}

.stories-archive__content {
  display: grid;
  gap: 20px;
  padding: 24px;
}

.stories-archive__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.stories-archive__header h2 {
  margin: 0;
  font-size: 20px;
}

.stories-archive__header p,
.stories-archive__status {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.stories-archive__list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.stories-archive__item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
  padding: 16px;
  color: var(--text);
  font: inherit;
  text-align: left;
  background: var(--bg-card, transparent);
  border: 1px solid var(--border);
  border-radius: 14px;
  cursor: pointer;
}

.stories-archive__item:hover {
  border-color: var(--accent);
}

.stories-archive__meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8px;
  width: 100%;
}

.stories-archive__kind {
  color: var(--muted);
  font-size: 11px;
}

.stories-archive__badge {
  padding: 3px 7px;
  color: var(--accent);
  font-size: 10px;
  line-height: 1.4;
  border: 1px solid currentColor;
  border-radius: 999px;
}

.stories-archive__title {
  display: -webkit-box;
  overflow: hidden;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.5;
  overflow-wrap: anywhere;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  line-clamp: 2;
}

.stories-archive__date {
  margin-top: auto;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.5;
}

@media (max-width: 480px) {
  .stories-archive__content {
    padding: 18px;
  }

  .stories-archive__header {
    flex-wrap: wrap;
  }

  .stories-archive__list {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (prefers-reduced-motion: reduce) {
  .profile-stories__create,
  .profile-stories__action {
    transition: none;
  }
}
</style>
