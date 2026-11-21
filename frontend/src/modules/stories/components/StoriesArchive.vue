<script setup>
import {
  computed,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue'
import { useAuthStore } from '@/modules/auth/stores/auth'
import StoryViewer from '@/modules/stories/components/StoryViewer.vue'
import {
  getStoryArchive,
  isStoryActive,
  isVideoStory,
  sortStories,
  storyErrorMessage,
} from '@/modules/stories/api/stories'

const auth = useAuthStore()

const stories = ref([])
const loading = ref(false)
const error = ref('')
const viewer = ref(null)
const now = ref(Date.now())

let disposed = false
let generation = 0
let expirationTimer = null

const items = computed(() => sortStories(stories.value).reverse())

function scheduleExpiration() {
  window.clearTimeout(expirationTimer)
  now.value = Date.now()

  const nextExpiration = stories.value
    .map((story) => Date.parse(story.expires_at))
    .filter((expiresAt) => Number.isFinite(expiresAt) && expiresAt > now.value)
    .sort((first, second) => first - second)[0]

  if (!nextExpiration) return

  expirationTimer = window.setTimeout(
    scheduleExpiration,
    Math.min(nextExpiration - now.value + 50, 2_147_483_647),
  )
}

async function load() {
  const accountId = auth.user?.user_id

  if (!accountId) return

  const requestGeneration = ++generation

  loading.value = true
  error.value = ''

  try {
    const result = await getStoryArchive()

    if (
      disposed ||
      requestGeneration !== generation ||
      String(auth.user?.user_id) !== String(accountId)
    ) {
      return
    }

    stories.value = result
    scheduleExpiration()
  } catch (cause) {
    if (!disposed && requestGeneration === generation) {
      error.value = storyErrorMessage(cause)
    }
  } finally {
    if (!disposed && requestGeneration === generation) {
      loading.value = false
    }
  }
}

function openStory(index) {
  const snapshot = [...items.value]

  if (!snapshot[index]) return

  viewer.value = {
    stories: snapshot,
    initialIndex: index,
  }
}

function onDeleted(storyId) {
  generation += 1
  loading.value = false
  error.value = ''

  stories.value = stories.value.filter(
    (story) => story.story_id !== storyId,
  )

  viewer.value = null
  scheduleExpiration()
}

function formatDate(value) {
  const date = new Date(value)

  if (!Number.isFinite(date.getTime())) return ''

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function onVisibilityChange() {
  if (document.hidden) return

  scheduleExpiration()

  if (!viewer.value && !loading.value) {
    load()
  }
}

watch(
  () => auth.user?.user_id,
  () => {
    generation += 1
    window.clearTimeout(expirationTimer)

    stories.value = []
    viewer.value = null
    loading.value = false
    error.value = ''
    now.value = Date.now()

    load()
  },
  { immediate: true },
)

onMounted(() => {
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  disposed = true
  generation += 1

  window.clearTimeout(expirationTimer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<template>
  <div class="stories-archive">
    <p v-if="loading" class="stories-archive__status" role="status">
      Загружаем истории…
    </p>

    <div v-else-if="error" role="alert">
      <p class="form-error">{{ error }}</p>

      <button
        class="btn btn-secondary btn-small"
        type="button"
        @click="load"
      >
        Повторить
      </button>
    </div>

    <p v-else-if="!items.length" class="stories-archive__status">
      Вы пока не публиковали истории.
    </p>

    <div v-else class="stories-archive__list">
      <button
        v-for="(story, index) in items"
        :key="story.story_id"
        class="stories-archive__item"
        type="button"
        :aria-label="`Открыть историю: ${story.title}`"
        @click="openStory(index)"
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

    <StoryViewer
      v-if="viewer"
      :stories="viewer.stories"
      :initial-index="viewer.initialIndex"
      own
      archive
      @close="viewer = null"
      @deleted="onDeleted"
    />
  </div>
</template>

<style scoped>
.stories-archive {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.stories-archive__status {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.stories-archive__list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 190px), 1fr));
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
  transition: border-color 150ms ease;
}

.stories-archive__item:hover {
  border-color: var(--accent);
}

.stories-archive__item:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 3px;
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

@media (prefers-reduced-motion: reduce) {
  .stories-archive__item {
    transition: none;
  }
}
</style>
