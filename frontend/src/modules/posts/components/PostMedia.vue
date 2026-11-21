<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { isPostVideo, postsApi } from '../api/posts'

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
})

const url = ref('')
const failed = ref(false)
const refreshing = ref(false)
const retryError = ref('')
const version = ref(0)
const video = computed(() => isPostVideo(url.value))

const frame = ref(null)
const player = ref(null)
const playing = ref(false)
const muted = ref(false)
const volume = ref(1)
const current = ref(0)
const duration = ref(0)
const playerMessage = ref('')

let generation = 0
let lastAudibleVolume = 1

const silent = computed(() => muted.value || volume.value === 0)
const audibleVolume = computed(() => (muted.value ? 0 : volume.value))
const volumePercent = computed(() => Math.round(audibleVolume.value * 100))

const progress = computed(() =>
  duration.value > 0
    ? Math.min(100, Math.max(0, (current.value / duration.value) * 100))
    : 0,
)

function resetPlayer() {
  playing.value = false
  muted.value = false
  volume.value = 1
  lastAudibleVolume = 1
  current.value = 0
  duration.value = 0
  playerMessage.value = ''
}

watch(
  [() => props.post.post_id, () => props.post.media_url],
  ([, mediaUrl]) => {
    generation += 1
    url.value = mediaUrl ?? ''
    failed.value = false
    refreshing.value = false
    retryError.value = ''
    version.value += 1
    resetPlayer()
  },
  { immediate: true },
)

function syncVolume(el) {
  muted.value = el.muted
  volume.value = el.volume

  if (el.volume > 0) {
    lastAudibleVolume = el.volume
  }
}

function syncPlayer(event) {
  const el = event.currentTarget

  playing.value = !el.paused && !el.ended
  current.value = el.currentTime
  duration.value = Number.isFinite(el.duration) ? el.duration : 0
  syncVolume(el)
}

function onMediaError() {
  playerMessage.value = ''
  failed.value = true
}

async function togglePlayback() {
  const el = player.value
  if (!el) return

  playerMessage.value = ''

  if (!el.paused && !el.ended) {
    el.pause()
    return
  }

  try {
    await el.play()
  } catch (cause) {
    if (player.value !== el || cause?.name === 'AbortError') return

    if (el.error || cause?.name === 'NotSupportedError') {
      onMediaError()
    } else {
      playerMessage.value = 'Не удалось запустить видео. Попробуйте ещё раз.'
    }
  }
}

function seek(event) {
  const el = player.value
  if (!el || duration.value <= 0) return

  const time = event.currentTarget.valueAsNumber
  if (!Number.isFinite(time)) return

  el.currentTime = time
  current.value = time
}

function setVolume(event) {
  const el = player.value
  const input = event.currentTarget
  if (!el || !Number.isFinite(input.valueAsNumber)) return

  const next = Math.min(1, Math.max(0, input.valueAsNumber / 100))
  playerMessage.value = ''

  if (next === 0) {
    // У нуля то же поведение, что у кнопки выключения звука:
    // предыдущая громкость остаётся доступной для восстановления.
    el.muted = true
  } else {
    el.volume = next
    el.muted = false

    if (Math.abs(el.volume - next) > 0.001) {
      playerMessage.value =
        'Браузер не даёт менять громкость плеера. Используйте кнопки громкости устройства.'
    }
  }

  syncVolume(el)
  input.value = String(volumePercent.value)
}

function toggleMute() {
  const el = player.value
  if (!el) return

  playerMessage.value = ''

  if (el.muted || el.volume === 0) {
    if (el.volume === 0) el.volume = lastAudibleVolume
    el.muted = false
  } else {
    el.muted = true
  }

  syncVolume(el)
}

async function toggleFullscreen() {
  const wrapper = frame.value
  const el = player.value
  if (!wrapper || !el) return

  playerMessage.value = ''

  if (document.fullscreenElement === wrapper) {
    try {
      await document.exitFullscreen()
    } catch {
      playerMessage.value = 'Не удалось выйти из полноэкранного режима.'
    }
    return
  }

  try {
    if (wrapper.requestFullscreen) {
      await wrapper.requestFullscreen()
      return
    }
  } catch {
    // Если контейнер раскрыть нельзя, пробуем режим самого видео.
  }

  if (player.value !== el) return

  try {
    if (el.webkitEnterFullscreen) {
      el.webkitEnterFullscreen()
      return
    }
  } catch {
    // Некоторые браузеры требуют, чтобы видео уже воспроизводилось.
  }

  playerMessage.value = 'Не удалось открыть полноэкранный режим.'
}

function formatTime(seconds) {
  const total = Math.max(0, Math.floor(seconds))
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const rest = String(total % 60).padStart(2, '0')

  return hours
    ? `${hours}:${String(minutes).padStart(2, '0')}:${rest}`
    : `${minutes}:${rest}`
}

async function refresh() {
  if (refreshing.value) return

  const request = ++generation
  const id = props.post.post_id

  refreshing.value = true
  retryError.value = ''

  try {
    const post = await postsApi.get(id)
    if (request !== generation) return

    if (!post.media_url) {
      url.value = ''
      retryError.value = 'У этой публикации больше нет вложения.'
      return
    }

    url.value = post.media_url
    version.value += 1
    resetPlayer()
    failed.value = false
  } catch (cause) {
    if (request !== generation) return

    retryError.value =
      cause?.status === 429
        ? 'Слишком много запросов. Попробуйте немного позже.'
        : 'Не удалось обновить ссылку на вложение.'
  } finally {
    if (request === generation) refreshing.value = false
  }
}

onBeforeUnmount(() => {
  generation += 1
})
</script>

<template>
  <div v-if="url || failed" class="post-media">
    <div v-if="failed" class="post-media__status">
      <p role="status">
        {{
          retryError ||
          'Не удалось открыть вложение. Ссылка могла истечь или браузер не поддерживает этот формат.'
        }}
      </p>

      <button
        v-if="url"
        class="btn btn-secondary btn-small"
        type="button"
        :disabled="refreshing"
        @click="refresh"
      >
        {{ refreshing ? 'Обновляем…' : 'Обновить ссылку' }}
      </button>
    </div>

    <div v-else-if="video" ref="frame" class="post-media__player">
      <video
        :key="`video:${version}`"
        ref="player"
        class="post-media__asset post-media__asset--video"
        :src="url"
        :aria-label="`Видео к публикации «${post.title}»`"
        playsinline
        preload="metadata"
        @click="togglePlayback"
        @loadedmetadata="syncPlayer"
        @durationchange="syncPlayer"
        @timeupdate="syncPlayer"
        @seeking="syncPlayer"
        @seeked="syncPlayer"
        @play="syncPlayer"
        @pause="syncPlayer"
        @ended="syncPlayer"
        @volumechange="syncPlayer"
        @error="onMediaError"
      />

      <div class="post-media__controls" role="group" aria-label="Управление видео">
        <button
          class="post-media__control post-media__control--play"
          type="button"
          :aria-label="playing ? 'Пауза' : 'Воспроизвести'"
          :title="playing ? 'Пауза' : 'Воспроизвести'"
          @click="togglePlayback"
        >
          <svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true">
            <path
              v-if="playing"
              d="M8 5h3v14H8zm5 0h3v14h-3z"
              fill="currentColor"
            />
            <path v-else d="M9 5v14l11-7z" fill="currentColor" />
          </svg>
        </button>

        <input
          class="post-media__slider post-media__seek"
          type="range"
          min="0"
          :max="duration || 1"
          :value="current"
          step="any"
          :disabled="!duration"
          :style="{ '--fill': `${progress}%` }"
          :aria-valuetext="`${formatTime(current)} из ${formatTime(duration)}`"
          aria-label="Позиция воспроизведения"
          @input="seek"
        />

        <span class="post-media__time" aria-hidden="true">
          {{ formatTime(current) }} / {{ formatTime(duration) }}
        </span>

        <div class="post-media__audio">
          <button
            class="post-media__control"
            type="button"
            :aria-label="silent ? 'Включить звук' : 'Выключить звук'"
            :title="silent ? 'Включить звук' : 'Выключить звук'"
            @click="toggleMute"
          >
            <svg
              viewBox="0 0 24 24"
              width="20"
              height="20"
              fill="none"
              stroke="currentColor"
              stroke-width="1.8"
              stroke-linecap="round"
              stroke-linejoin="round"
              aria-hidden="true"
            >
              <path d="M4 9v6h4l5 4V5L8 9z" />
              <path v-if="silent" d="m16 9 5 6m0-6-5 6" />
              <path v-else d="M16 9a4 4 0 0 1 0 6m2-8a7 7 0 0 1 0 10" />
            </svg>
          </button>

          <input
            class="post-media__slider post-media__volume"
            type="range"
            min="0"
            max="100"
            step="1"
            :value="volumePercent"
            :style="{ '--fill': `${volumePercent}%` }"
            :aria-valuetext="`${volumePercent}%`"
            :title="`Громкость: ${volumePercent}%`"
            aria-label="Громкость"
            @input="setVolume"
          />
        </div>

        <button
          class="post-media__control"
          type="button"
          aria-label="Переключить полноэкранный режим"
          title="Полноэкранный режим"
          @click="toggleFullscreen"
        >
          <svg
            viewBox="0 0 24 24"
            width="20"
            height="20"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            stroke-linecap="round"
            stroke-linejoin="round"
            aria-hidden="true"
          >
            <path d="M9 4H4v5m11-5h5v5M4 15v5h5m11-5v5h-5" />
          </svg>
        </button>
      </div>

      <p v-if="playerMessage" class="post-media__notice" role="status">
        {{ playerMessage }}
      </p>
    </div>

    <img
      v-else
      :key="`image:${version}`"
      class="post-media__asset post-media__asset--image"
      :src="url"
      :alt="`Изображение к публикации «${post.title}»`"
      loading="lazy"
      decoding="async"
      @error="onMediaError"
    />
  </div>
</template>

<style scoped>
.post-media {
  box-sizing: border-box;
  width: min(100%, var(--post-media-width, 560px));
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: color-mix(in srgb, currentColor 4%, transparent);
  container-type: inline-size;
}

.post-media__asset {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
}

.post-media__asset--image {
  max-height: var(--post-media-image-height, min(360px, 52vh));
}

.post-media__asset--video {
  max-height: var(--post-media-video-height, min(320px, 48vh));
  aspect-ratio: 16 / 9;
  background: #111318;
  cursor: pointer;
}

.post-media__player {
  --player-accent: var(--accent, #42c99a);
  --player-track: #555b66;

  min-width: 0;
  color: #f3f4f6;
  background: #181b21;
}

.post-media__controls {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  padding: 4px 8px;
}

.post-media__control {
  display: grid;
  flex: 0 0 44px;
  width: 44px;
  height: 44px;
  padding: 0;
  place-items: center;
  color: inherit;
  background: transparent;
  border: 0;
  border-radius: 8px;
  cursor: pointer;
}

.post-media__control--play {
  color: color-mix(in srgb, var(--player-accent) 75%, white);
  background: color-mix(in srgb, var(--player-accent) 22%, transparent);
}

.post-media__control:hover:not(:disabled) {
  background: color-mix(in srgb, var(--player-accent) 32%, transparent);
}

.post-media__control:focus-visible,
.post-media__slider:focus-visible {
  outline: 2px solid color-mix(in srgb, var(--player-accent) 75%, white);
  outline-offset: 2px;
}

.post-media__slider {
  --slider-bg: linear-gradient(
    to right,
    var(--player-accent) 0% var(--fill, 0%),
    var(--player-track) var(--fill, 0%) 100%
  );

  display: block;
  min-width: 0;
  height: 44px;
  margin: 0;
  padding: 0;
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  cursor: pointer;
}

.post-media__seek {
  flex: 1 1 0;
  width: 100%;
}

.post-media__audio {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 2px;
}

.post-media__volume {
  width: 72px;
}

.post-media__slider:disabled {
  opacity: 0.5;
  cursor: default;
}

.post-media__slider::-webkit-slider-runnable-track {
  height: 5px;
  border-radius: 999px;
  background: var(--slider-bg);
}

.post-media__slider::-webkit-slider-thumb {
  box-sizing: border-box;
  width: 14px;
  height: 14px;
  margin-top: -4.5px;
  -webkit-appearance: none;
  appearance: none;
  border: 2px solid #f3f4f6;
  border-radius: 50%;
  background: var(--player-accent);
}

.post-media__slider::-moz-range-track {
  height: 5px;
  border-radius: 999px;
  background: var(--slider-bg);
}

.post-media__slider::-moz-range-thumb {
  box-sizing: border-box;
  width: 14px;
  height: 14px;
  border: 2px solid #f3f4f6;
  border-radius: 50%;
  background: var(--player-accent);
}

.post-media__time {
  flex: 0 0 auto;
  color: #c6cad2;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.post-media__player:fullscreen {
  display: flex;
  flex-direction: column;
  justify-content: center;
  width: 100%;
  height: 100%;
  background: #111318;
}

.post-media__player:fullscreen .post-media__asset--video {
  flex: 1 1 0;
  min-height: 0;
  max-height: none;
  aspect-ratio: auto;
}

.post-media__notice {
  margin: 0;
  padding: 0 12px 10px;
  color: #c6cad2;
  font-size: 12px;
}

.post-media__status {
  padding: 14px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.post-media__status p {
  margin: 0 0 8px;
}

@media (max-width: 600px) {
  .post-media__asset--image {
    max-height: var(--post-media-image-height, min(280px, 44vh));
    max-height: var(--post-media-image-height, min(280px, 44svh));
  }

  .post-media__asset--video {
    max-height: var(--post-media-video-height, min(240px, 40vh));
    max-height: var(--post-media-video-height, min(240px, 40svh));
  }
}

@container (max-width: 400px) {
  .post-media__controls {
    gap: 4px;
  }

  .post-media__time {
    display: none;
  }

  .post-media__volume {
    width: 52px;
  }
}

@container (max-width: 245px) {
  .post-media__controls {
    flex-wrap: wrap;
  }

  .post-media__seek {
    flex: 1 0 48px;
  }
}
</style>
