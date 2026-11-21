<script setup>
import {
  computed,
  nextTick,
  onBeforeUnmount,
  onMounted,
  ref,
  watch,
} from 'vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import {
  deleteStory,
  getStory,
  isVideoStory,
  storyErrorMessage,
} from '@/modules/stories/api/stories'

const props = defineProps({
  stories: {
    type: Array,
    required: true,
  },
  initialIndex: {
    type: Number,
    default: 0,
  },
  own: {
    type: Boolean,
    default: false,
  },
  archive: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close', 'deleted'])

const IMAGE_DURATION = 6000

const dialog = ref(null)
const video = ref(null)
const items = ref([...props.stories])
const index = ref(
  Math.max(0, Math.min(props.initialIndex, props.stories.length - 1)),
)

const ready = ref(false)
const paused = ref(false)
const hidden = ref(document.hidden)
const progress = ref(0)
const mediaError = ref(false)
const error = ref('')
const busy = ref(false)
const refreshing = ref(false)
const muted = ref(true)
const mediaVersion = ref(0)

let disposed = false
let closing = false
let interval = null
let lastTick = 0
let generation = 0

const current = computed(() => items.value[index.value] || null)

const videoStory = computed(
  () => Boolean(current.value && isVideoStory(current.value)),
)

const controlsDisabled = computed(
  () => busy.value || refreshing.value,
)

const canRun = computed(
  () =>
    ready.value &&
    !paused.value &&
    !hidden.value &&
    !mediaError.value &&
    !controlsDisabled.value,
)

const isLastStory = computed(
  () => index.value === items.value.length - 1,
)

const formattedDate = computed(() => {
  if (!current.value) return ''

  const date = new Date(current.value.created_at)

  if (!Number.isFinite(date.getTime())) return ''

  return new Intl.DateTimeFormat('ru-RU', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
})

function close() {
  if (busy.value || closing) return

  closing = true
  video.value?.pause()
  emit('close')
}

function move(step) {
  if (controlsDisabled.value || closing) return

  const nextIndex = index.value + step

  if (nextIndex < 0) return

  if (nextIndex >= items.value.length) {
    close()
    return
  }

  video.value?.pause()
  index.value = nextIndex
}

function togglePause() {
  if (controlsDisabled.value) return

  paused.value = !paused.value
}

function toggleSound() {
  if (controlsDisabled.value) return

  muted.value = !muted.value
}

async function syncVideoPlayback() {
  const requestGeneration = generation

  await nextTick()

  if (
    disposed ||
    closing ||
    requestGeneration !== generation
  ) {
    return
  }

  const element = video.value

  if (!element || !videoStory.value) return

  if (!canRun.value) {
    element.pause()
    return
  }

  try {
    await element.play()
  } catch {
    if (
      !disposed &&
      !closing &&
      requestGeneration === generation &&
      video.value === element &&
      canRun.value
    ) {
      paused.value = true
    }
  }
}

function onVideoTimeUpdate() {
  const element = video.value

  if (
    !element ||
    !Number.isFinite(element.duration) ||
    element.duration <= 0
  ) {
    return
  }

  progress.value = Math.min(
    100,
    (element.currentTime / element.duration) * 100,
  )
}

function onMediaError() {
  ready.value = false
  mediaError.value = true
}

function onVisibilityChange() {
  lastTick = performance.now()
  hidden.value = document.hidden
}

function onKeydown(event) {
  if (event.defaultPrevented) return

  if (
    event.target instanceof Element &&
    event.target.closest(
      'input, textarea, select, [contenteditable="true"]',
    )
  ) {
    return
  }

  if (event.key === 'ArrowRight') {
    event.preventDefault()
    move(1)
    return
  }

  if (event.key === 'ArrowLeft') {
    event.preventDefault()
    move(-1)
    return
  }

  if (event.code === 'Space') {
    if (
      event.target instanceof Element &&
      event.target.closest('button, a, video')
    ) {
      return
    }

    event.preventDefault()
    togglePause()
  }
}

async function refreshMedia() {
  if (!current.value || controlsDisabled.value) return

  const storyId = current.value.story_id
  const requestGeneration = generation

  refreshing.value = true
  error.value = ''

  try {
    const updated = await getStory(storyId, {
      archive: props.archive,
    })

    if (
      disposed ||
      closing ||
      requestGeneration !== generation ||
      current.value?.story_id !== storyId
    ) {
      return
    }

    ready.value = false
    progress.value = 0
    mediaError.value = false
    items.value[index.value] = updated
    mediaVersion.value += 1
  } catch (cause) {
    if (
      !disposed &&
      !closing &&
      requestGeneration === generation
    ) {
      error.value = storyErrorMessage(cause)
    }
  } finally {
    if (!disposed && requestGeneration === generation) {
      refreshing.value = false
    }
  }
}

async function removeCurrent() {
  if (
    !props.own ||
    !current.value ||
    controlsDisabled.value
  ) {
    return
  }

  const wasPaused = paused.value

  paused.value = true
  video.value?.pause()

  const confirmed = window.confirm(
    'Удалить эту историю? Восстановить её будет нельзя.',
  )

  if (!confirmed) {
    paused.value = wasPaused
    syncVideoPlayback()
    return
  }

  const storyId = current.value.story_id

  busy.value = true
  error.value = ''

  try {
    await deleteStory(storyId)

    if (!disposed) {
      closing = true
      emit('deleted', storyId)
    }
  } catch (cause) {
    if (!disposed) {
      error.value = storyErrorMessage(cause)
    }
  } finally {
    if (!disposed) {
      busy.value = false
    }
  }
}

watch(
  index,
  () => {
    generation += 1
    ready.value = false
    progress.value = 0
    mediaError.value = false
    error.value = ''
    refreshing.value = false
    mediaVersion.value = 0
    lastTick = performance.now()
  },
  { flush: 'sync' },
)

watch(
  [canRun, videoStory],
  () => {
    syncVideoPlayback()
  },
)

onMounted(() => {
  dialog.value?.showModal()

  if (!current.value) {
    close()
    return
  }

  document.addEventListener(
    'visibilitychange',
    onVisibilityChange,
  )

  lastTick = performance.now()

  interval = window.setInterval(() => {
    const tick = performance.now()
    const elapsed = Math.min(tick - lastTick, 500)

    lastTick = tick

    if (
      closing ||
      !canRun.value ||
      videoStory.value
    ) {
      return
    }

    progress.value = Math.min(
      100,
      progress.value + (elapsed / IMAGE_DURATION) * 100,
    )

    if (progress.value >= 100) {
      move(1)
    }
  }, 100)
})

onBeforeUnmount(() => {
  disposed = true
  generation += 1

  window.clearInterval(interval)

  document.removeEventListener(
    'visibilitychange',
    onVisibilityChange,
  )

  video.value?.pause()
  dialog.value?.close()
})
</script>

<template>
  <dialog
    ref="dialog"
    class="story-viewer"
    aria-labelledby="story-viewer-title"
    tabindex="-1"
    @cancel.prevent="close"
    @keydown="onKeydown"
  >
    <div v-if="current" class="story-viewer__content">
      <div class="story-viewer__progress" aria-hidden="true">
        <span
          v-for="(story, storyIndex) in items"
          :key="story.story_id"
          class="story-viewer__segment"
        >
          <span
            :style="{
              width:
                storyIndex < index
                  ? '100%'
                  : storyIndex === index
                    ? `${progress}%`
                    : '0%',
            }"
          />
        </span>
      </div>

      <header class="story-viewer__header">
        <div class="story-viewer__author">
          <div class="story-viewer__author-avatar">
            <UserAvatar :user="current.author" :size="36" />
          </div>

          <div class="story-viewer__author-copy">
            <strong
              :title="
                current.author.name || current.author.username
              "
            >
              {{ current.author.name || current.author.username }}
            </strong>

            <time :datetime="current.created_at">
              {{ formattedDate }}
            </time>
          </div>
        </div>

        <div
          class="story-viewer__tools"
          role="group"
          aria-label="Управление историей"
        >
          <button
            class="story-viewer__icon-button"
            type="button"
            :disabled="controlsDisabled"
            :aria-label="paused ? 'Продолжить' : 'Пауза'"
            :title="paused ? 'Продолжить' : 'Пауза'"
            @click="togglePause"
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
                v-if="paused"
                d="m9 5 11 7-11 7V5Z"
                fill="currentColor"
              />

              <path
                v-else
                d="M8 5v14M16 5v14"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
              />
            </svg>
          </button>

          <button
            v-if="videoStory"
            class="story-viewer__icon-button"
            type="button"
            :disabled="controlsDisabled"
            :aria-label="
              muted ? 'Включить звук' : 'Выключить звук'
            "
            :title="
              muted ? 'Включить звук' : 'Выключить звук'
            "
            @click="toggleSound"
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
                d="M11 5 6 9H3v6h3l5 4V5Z"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />

              <path
                v-if="muted"
                d="m16 9 5 6m0-6-5 6"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
              />

              <g v-else>
                <path
                  d="M15 8a6 6 0 0 1 0 8"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                />
                <path
                  d="M18 5a10 10 0 0 1 0 14"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                />
              </g>

              <path
                v-if="muted"
                d="m3 3 18 18"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
              />
            </svg>
          </button>

          <button
            v-if="own"
            class="story-viewer__icon-button story-viewer__icon-button--danger"
            type="button"
            :disabled="controlsDisabled"
            :aria-label="busy ? 'Удаляем историю' : 'Удалить историю'"
            :title="busy ? 'Удаляем…' : 'Удалить историю'"
            @click="removeCurrent"
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
                d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6"
                stroke="currentColor"
                stroke-width="1.8"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>

          <button
            class="story-viewer__icon-button"
            type="button"
            :disabled="busy"
            aria-label="Закрыть просмотр"
            title="Закрыть"
            @click="close"
          >
            <svg
              width="21"
              height="21"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="m6 6 12 12M18 6 6 18"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              />
            </svg>
          </button>
        </div>
      </header>

      <div class="story-viewer__media">
        <video
          v-if="videoStory && !mediaError"
          :key="`video:${current.story_id}:${mediaVersion}`"
          ref="video"
          class="story-viewer__asset"
          :src="current.media_url"
          :muted="muted"
          playsinline
          preload="auto"
          @loadeddata="ready = true"
          @canplay="ready = true"
          @waiting="ready = false"
          @timeupdate="onVideoTimeUpdate"
          @ended="move(1)"
          @error="onMediaError"
        />

        <img
          v-else-if="!mediaError"
          :key="`image:${current.story_id}:${mediaVersion}`"
          class="story-viewer__asset"
          :src="current.media_url"
          :alt="current.title"
          @load="ready = true"
          @error="onMediaError"
        />

        <div
          v-if="mediaError"
          class="story-viewer__media-status"
          role="alert"
        >
          <p>
            Не удалось открыть медиа. Ссылка могла истечь,
            либо формат не поддерживается браузером.
          </p>

          <button
            class="story-viewer__retry"
            type="button"
            :disabled="controlsDisabled"
            @click="refreshMedia"
          >
            {{ refreshing ? 'Обновляем…' : 'Обновить ссылку' }}
          </button>
        </div>

        <p
          v-else-if="!ready"
          class="story-viewer__loading"
          role="status"
        >
          Загружаем…
        </p>

        <button
          v-if="index > 0"
          class="story-viewer__navigation story-viewer__navigation--previous"
          type="button"
          :disabled="controlsDisabled"
          aria-label="Предыдущая история"
          title="Предыдущая история"
          @click="move(-1)"
        >
          <span class="story-viewer__arrow">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="m14 6-6 6 6 6"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
        </button>

        <button
          class="story-viewer__navigation story-viewer__navigation--next"
          type="button"
          :disabled="controlsDisabled"
          :aria-label="
            isLastStory ? 'Завершить просмотр' : 'Следующая история'
          "
          :title="
            isLastStory ? 'Завершить просмотр' : 'Следующая история'
          "
          @click="move(1)"
        >
          <span class="story-viewer__arrow">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
              focusable="false"
            >
              <path
                d="m10 6 6 6-6 6"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>
        </button>
      </div>

      <footer class="story-viewer__footer">
        <h2 id="story-viewer-title">{{ current.title }}</h2>

        <p class="story-viewer__counter">
          {{ index + 1 }} / {{ items.length }}
          <span v-if="archive"> · Архив</span>
        </p>

        <p v-if="error" class="story-viewer__error" role="alert">
          {{ error }}
        </p>
      </footer>
    </div>
  </dialog>
</template>

<style scoped>
.story-viewer {
  width: min(480px, calc(100vw - 24px));
  height: min(820px, calc(100dvh - 24px));
  max-width: none;
  max-height: none;
  margin: auto;
  padding: 0;
  overflow: hidden;
  color: #fff;
  background: #111318;
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 20px;
}

.story-viewer::backdrop {
  background: rgb(0 0 0 / 86%);
}

.story-viewer__content {
  display: grid;
  grid-template-rows: auto auto minmax(0, 1fr) auto;
  height: 100%;
}

.story-viewer__progress {
  display: flex;
  gap: 4px;
  padding: 14px 14px 0;
}

.story-viewer__segment {
  flex: 1;
  height: 3px;
  overflow: hidden;
  background: rgb(255 255 255 / 25%);
  border-radius: 4px;
}

.story-viewer__segment > span {
  display: block;
  height: 100%;
  background: var(--accent, #42c99a);
}

.story-viewer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px;
}

.story-viewer__author {
  display: flex;
  flex: 1 1 auto;
  align-items: center;
  gap: 9px;
  min-width: 0;
}

.story-viewer__author-avatar {
  display: inline-flex;
  flex: 0 0 auto;
}

.story-viewer__author-copy {
  min-width: 0;
}

.story-viewer__author strong {
  display: block;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.story-viewer__author time {
  display: block;
  margin-top: 3px;
  color: #b8bdc7;
  font-size: 10px;
  line-height: 1.4;
}

.story-viewer__tools {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 2px;
}

.story-viewer__icon-button {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 40px;
  padding: 0;
  color: #fff;
  background: transparent;
  border: 0;
  border-radius: 10px;
  cursor: pointer;
  transition: background-color 150ms ease;
}

.story-viewer__icon-button:hover:not(:disabled) {
  background: rgb(255 255 255 / 12%);
}

.story-viewer__icon-button--danger:hover:not(:disabled) {
  color: #ffb0b0;
  background: rgb(255 100 100 / 12%);
}

.story-viewer__icon-button:disabled,
.story-viewer__retry:disabled {
  opacity: 0.45;
  cursor: default;
}

.story-viewer__icon-button:focus-visible,
.story-viewer__retry:focus-visible {
  outline: 2px solid var(--accent, #42c99a);
  outline-offset: 2px;
}

.story-viewer__media {
  position: relative;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
}

.story-viewer__asset {
  position: absolute;
  inset: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.story-viewer__loading {
  position: absolute;
  top: 50%;
  left: 50%;
  margin: 0;
  padding: 8px 12px;
  font-size: 13px;
  white-space: nowrap;
  background: rgb(0 0 0 / 65%);
  border-radius: 8px;
  transform: translate(-50%, -50%);
  pointer-events: none;
}

.story-viewer__media-status {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  height: 100%;
  padding: 24px max(24px, 21%);
  color: #d5d8df;
  font-size: 13px;
  line-height: 1.6;
  text-align: center;
  overflow: auto;
}

.story-viewer__media-status p {
  margin: 0 0 16px;
}

.story-viewer__retry {
  padding: 9px 12px;
  color: #fff;
  font: inherit;
  font-size: 12px;
  background: rgb(255 255 255 / 10%);
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 10px;
  cursor: pointer;
}

.story-viewer__retry:hover:not(:disabled) {
  background: rgb(255 255 255 / 18%);
}

.story-viewer__navigation {
  position: absolute;
  top: 0;
  bottom: 0;
  z-index: 1;
  display: flex;
  align-items: center;
  width: 20%;
  min-width: 44px;
  padding: 0 10px;
  color: #fff;
  background: transparent;
  border: 0;
  cursor: pointer;
  -webkit-tap-highlight-color: transparent;
}

.story-viewer__navigation--previous {
  left: 0;
  justify-content: flex-start;
}

.story-viewer__navigation--next {
  right: 0;
  justify-content: flex-end;
}

.story-viewer__arrow {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  background: rgb(0 0 0 / 30%);
  border: 1px solid rgb(255 255 255 / 16%);
  border-radius: 50%;
  opacity: 0.7;
  transition:
    opacity 150ms ease,
    background-color 150ms ease;
}

.story-viewer__navigation:hover:not(:disabled)
  .story-viewer__arrow {
  background: rgb(0 0 0 / 55%);
  opacity: 1;
}

.story-viewer__navigation:focus-visible {
  outline: 0;
}

.story-viewer__navigation:focus-visible .story-viewer__arrow {
  outline: 2px solid var(--accent, #42c99a);
  outline-offset: 3px;
  opacity: 1;
}

.story-viewer__navigation:disabled {
  cursor: default;
}

.story-viewer__navigation:disabled .story-viewer__arrow {
  opacity: 0.25;
}

.story-viewer__footer {
  max-height: 25dvh;
  padding: 16px;
  overflow: auto;
}

.story-viewer__footer h2 {
  margin: 0;
  font-size: 17px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

.story-viewer__counter {
  margin: 6px 0 0;
  color: #b8bdc7;
  font-size: 12px;
  line-height: 1.5;
}

.story-viewer__error {
  margin: 12px 0 0;
  color: #ffb0b0;
  font-size: 13px;
  line-height: 1.5;
  overflow-wrap: anywhere;
}

@media (max-width: 520px) {
  .story-viewer {
    width: 100vw;
    height: 100dvh;
    border: 0;
    border-radius: 0;
  }

  .story-viewer__progress {
    padding-top: max(12px, env(safe-area-inset-top));
  }

  .story-viewer__footer {
    padding-bottom: max(16px, env(safe-area-inset-bottom));
  }
}

@media (max-width: 360px) {
  .story-viewer__header {
    gap: 4px;
    padding-right: 8px;
    padding-left: 8px;
  }

  .story-viewer__author {
    gap: 6px;
  }

  .story-viewer__icon-button {
    width: 32px;
  }

  .story-viewer__tools {
    gap: 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .story-viewer__icon-button,
  .story-viewer__arrow {
    transition: none;
  }
}
</style>
