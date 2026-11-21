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
  getUserStories,
  isStoryActive,
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

const stories = ref([])
const loading = ref(false)
const error = ref('')
const composerOpen = ref(false)
const viewer = ref(null)
const now = ref(Date.now())

let disposed = false
let generation = 0
let expirationTimer = null

const own = computed(
  () =>
    Boolean(auth.user?.user_id) &&
    String(auth.user.user_id) === String(props.user.user_id),
)

const active = computed(() =>
  sortStories(
    stories.value.filter((story) => isStoryActive(story, now.value)),
  ),
)

const hasStories = computed(() => active.value.length > 0)

const showCreate = computed(
  () => own.value && active.value.length < STORY_LIMIT,
)

const canCreate = computed(
  () => showCreate.value && !loading.value,
)

const avatarLabel = computed(() => {
  const name = props.user.name || props.user.username

  return hasStories.value
    ? `Открыть истории пользователя ${name}. Активных: ${active.value.length}`
    : `Аватар пользователя ${name}. Активных историй нет`
})

const createLabel = computed(() =>
  loading.value ? 'Загружаем список историй' : 'Создать историю',
)

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

async function loadActive() {
  const username = props.user.username
  const accountId = auth.user?.user_id

  if (!username || !accountId) return

  const requestGeneration = ++generation

  loading.value = true
  error.value = ''

  try {
    const result = await getUserStories(username)

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

function openActive() {
  now.value = Date.now()

  if (!active.value.length) return

  viewer.value = [...active.value]
}

function openComposer() {
  now.value = Date.now()

  if (!canCreate.value) return

  composerOpen.value = true
}

function onCreated(story) {
  generation += 1
  loading.value = false
  composerOpen.value = false
  error.value = ''

  stories.value = [
    ...stories.value.filter((item) => item.story_id !== story.story_id),
    story,
  ]

  scheduleExpiration()
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

function onVisibilityChange() {
  if (document.hidden) return

  scheduleExpiration()

  if (!viewer.value && !composerOpen.value && !loading.value) {
    loadActive()
  }
}

watch(
  [
    () => props.user.user_id,
    () => props.user.username,
    () => auth.user?.user_id,
  ],
  () => {
    generation += 1
    window.clearTimeout(expirationTimer)

    stories.value = []
    loading.value = false
    error.value = ''
    composerOpen.value = false
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
  generation += 1

  window.clearTimeout(expirationTimer)
  document.removeEventListener('visibilitychange', onVisibilityChange)
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
        v-if="showCreate"
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

    <div v-if="error" class="profile-stories__error" role="alert">
      <p>{{ error }}</p>

      <button
        class="profile-stories__retry"
        type="button"
        :disabled="loading"
        @click="loadActive"
      >
        Повторить загрузку историй
      </button>
    </div>

    <StoryComposer
      v-if="composerOpen && own"
      @close="composerOpen = false"
      @created="onCreated"
    />

    <StoryViewer
      v-if="viewer"
      :stories="viewer"
      :own="own"
      @close="viewer = null"
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
.profile-stories__retry:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
}

.profile-stories__error {
  width: 100%;
  color: #e57373;
  font-size: 12px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.profile-stories__error p {
  margin: 0;
}

.profile-stories__retry {
  display: block;
  margin-top: 6px;
  padding: 0;
  color: var(--text);
  font: inherit;
  text-align: left;
  text-decoration: underline;
  background: transparent;
  border: 0;
  cursor: pointer;
}

.profile-stories__retry:disabled {
  opacity: 0.5;
  cursor: default;
}

@media (prefers-reduced-motion: reduce) {
  .profile-stories__create {
    transition: none;
  }
}
</style>
