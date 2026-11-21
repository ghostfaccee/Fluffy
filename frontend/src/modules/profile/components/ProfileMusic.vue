<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useMusicUpload } from '@/modules/profile/composables/useMusicUpload'
import { useMusicMetadata } from '@/modules/profile/composables/useMusicMetadata'

const props = defineProps({
  musicUrl: {
    type: String,
    default: null,
  },
  editable: {
    type: Boolean,
    default: false,
  },
})

const {
  uploading,
  removing,
  busy,
  error,
  upload,
  remove,
} = useMusicUpload()

const {
  title,
  artist,
  coverUrl,
  loading: metadataLoading,
  notice: metadataNotice,
} = useMusicMetadata(() => props.musicUrl)

const audio = ref(null)
const fileInput = ref(null)

const playing = ref(false)
const buffering = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(0.8)
const playbackError = ref('')
const successMessage = ref('')
const coverFailed = ref(false)

let playRequest = 0

const hasMusic = computed(() => Boolean(props.musicUrl))

const canSeek = computed(
  () => Number.isFinite(duration.value) && duration.value > 0,
)

const progress = computed(() => {
  if (!canSeek.value) return 0

  return Math.min(
    100,
    Math.max(0, (currentTime.value / duration.value) * 100),
  )
})

const trackTitle = computed(() => {
  if (!hasMusic.value) return 'Ваш любимый трек'
  if (title.value) return title.value
  if (metadataLoading.value) return 'Читаем название…'

  return 'Музыка профиля'
})

const trackArtist = computed(() => {
  if (!hasMusic.value) return 'Добавьте музыку в свой профиль'
  if (artist.value) return artist.value
  if (metadataLoading.value) return 'Загружаем теги'

  return 'Исполнитель не указан'
})

const playbackStatus = computed(() => {
  if (buffering.value) return 'Загружаем аудио…'
  if (playing.value) return 'Сейчас играет'

  return ''
})

watch(coverUrl, () => {
  coverFailed.value = false
})

watch(
  () => props.musicUrl,
  () => {
    playRequest += 1
    audio.value?.pause()

    playing.value = false
    buffering.value = false
    currentTime.value = 0
    duration.value = 0
    playbackError.value = ''
  },
  { flush: 'pre' },
)

function formatTime(value) {
  if (!Number.isFinite(value) || value < 0) return '0:00'

  const seconds = Math.floor(value)
  const minutes = Math.floor(seconds / 60)

  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}

function updateDuration() {
  const value = audio.value?.duration

  duration.value = Number.isFinite(value) && value > 0 ? value : 0
}

function updateTime() {
  currentTime.value = audio.value?.currentTime || 0
}

function applyVolume() {
  if (audio.value) {
    audio.value.volume = volume.value
  }
}

function onPlaying() {
  playing.value = true
  buffering.value = false
  playbackError.value = ''
}

function onPause() {
  playing.value = false
  buffering.value = false
}

function onEnded() {
  playing.value = false
  buffering.value = false
  updateTime()
}

function onWaiting() {
  if (audio.value && !audio.value.paused) {
    buffering.value = true
  }
}

function onMediaError() {
  const code = audio.value?.error?.code

  playing.value = false
  buffering.value = false

  switch (code) {
    case 1:
      playbackError.value =
        'Загрузка аудио прервана. Попробуйте ещё раз.'
      break

    case 2:
      playbackError.value =
        'Не удалось получить аудио по сети. Проверьте подключение.'
      break

    case 3:
      playbackError.value =
        'Не удалось декодировать аудиофайл. Возможно, он повреждён или использует неподдерживаемый кодек.'
      break

    case 4:
      playbackError.value =
        'Аудиофайл недоступен или не распознан. Попробуйте обновить профиль.'
      break

    default:
      playbackError.value =
        'Не удалось загрузить аудиофайл. Попробуйте ещё раз.'
  }
}

async function startPlayback(reload = false) {
  const element = audio.value

  if (!element || !hasMusic.value) return

  const request = ++playRequest

  playbackError.value = ''
  buffering.value = true
  element.volume = volume.value

  if (reload || element.error) {
    element.load()
  }

  try {
    await element.play()

    if (request !== playRequest || element !== audio.value) return

    playing.value = !element.paused
    buffering.value = false
  } catch (cause) {
    if (request !== playRequest || element !== audio.value) return

    buffering.value = false

    if (cause?.name === 'AbortError') return

    if (element.error) {
      onMediaError()
      return
    }

    if (cause?.name === 'NotAllowedError') {
      playbackError.value =
        'Браузер запретил воспроизведение. Проверьте разрешения сайта.'
      return
    }

    playbackError.value =
      'Не удалось начать воспроизведение. Попробуйте ещё раз.'
  }
}

function togglePlayback() {
  const element = audio.value

  if (!element) return

  if (!element.paused) {
    playRequest += 1
    element.pause()
    return
  }

  void startPlayback()
}

function seek(event) {
  const element = audio.value
  const value = Number(event.target.value)

  if (!element || !canSeek.value || !Number.isFinite(value)) return

  try {
    element.currentTime = value
    currentTime.value = element.currentTime
  } catch {
    // Некоторые источники не позволяют перемотку до загрузки данных.
  }
}

function changeVolume(event) {
  const value = Number(event.target.value)

  if (!Number.isFinite(value)) return

  volume.value = Math.min(1, Math.max(0, value))
  applyVolume()
}

function pickFile() {
  if (!props.editable || busy.value) return

  fileInput.value?.click()
}

async function onFileChange(event) {
  const file = event.target.files?.[0]

  event.target.value = ''

  if (!file || !props.editable || busy.value) return

  successMessage.value = ''

  const replacing = hasMusic.value
  const saved = await upload(file)

  if (saved) {
    successMessage.value = replacing
      ? 'Музыка заменена.'
      : 'Музыка добавлена.'
  }
}

async function onRemove() {
  if (!props.editable || busy.value || !hasMusic.value) return

  successMessage.value = ''

  const removed = await remove()

  if (removed) {
    successMessage.value = 'Музыка удалена.'
  }
}

onBeforeUnmount(() => {
  playRequest += 1
  audio.value?.pause()
})
</script>

<template>
  <section
    v-if="editable || hasMusic"
    class="app-section music-card"
    aria-label="Музыка профиля"
    :aria-busy="busy"
  >
    <header class="music-card__header">
      <h2 class="music-card__heading">Музыка</h2>

      <span
        v-if="playing"
        class="music-card__equalizer"
        aria-label="Воспроизводится"
      >
        <span></span>
        <span></span>
        <span></span>
      </span>

      <span v-else class="music-card__badge">В профиле</span>
    </header>

    <div class="music-card__track">
      <div
        class="music-card__art"
        :class="{ 'music-card__art--empty': !coverUrl || coverFailed }"
      >
        <img
          v-if="coverUrl && !coverFailed"
          :src="coverUrl"
          class="music-card__cover"
          :alt="`Обложка: ${trackTitle}`"
          @error="coverFailed = true"
        />

        <svg
          v-else
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.6"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M9 18V5l11-2v13" />
          <path d="M9 9l11-2" />
          <ellipse cx="6" cy="18" rx="3" ry="2.5" />
          <ellipse cx="17" cy="16" rx="3" ry="2.5" />
        </svg>
      </div>

      <div class="music-card__description">
        <p class="music-card__title" :title="trackTitle">
          {{ trackTitle }}
        </p>

        <p class="music-card__artist" :title="trackArtist">
          {{ trackArtist }}
        </p>

        <p
          v-if="playbackStatus"
          class="music-card__status"
          role="status"
        >
          {{ playbackStatus }}
        </p>
      </div>
    </div>

    <template v-if="hasMusic">
      <audio
        :key="musicUrl"
        ref="audio"
        :src="musicUrl"
        preload="none"
        @loadedmetadata="updateDuration(); applyVolume()"
        @durationchange="updateDuration"
        @timeupdate="updateTime"
        @play="playing = true"
        @playing="onPlaying"
        @pause="onPause"
        @ended="onEnded"
        @waiting="onWaiting"
        @canplay="buffering = false"
        @error="onMediaError"
      />

      <div class="music-card__controls">
        <button
          class="music-card__play"
          type="button"
          :aria-label="playing ? 'Приостановить музыку' : 'Включить музыку'"
          :aria-pressed="playing"
          @click="togglePlayback"
        >
          <svg
            v-if="!playing"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M8 5.5a1 1 0 0 1 1.52-.85l10 6.5a1 1 0 0 1 0 1.7l-10 6.5A1 1 0 0 1 8 18.5z" />
          </svg>

          <svg
            v-else
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <rect x="6" y="5" width="4" height="14" rx="1" />
            <rect x="14" y="5" width="4" height="14" rx="1" />
          </svg>
        </button>

        <div class="music-card__timeline">
          <input
            class="music-card__range"
            type="range"
            min="0"
            :max="canSeek ? duration : 1"
            step="0.1"
            :value="canSeek ? Math.min(currentTime, duration) : 0"
            :disabled="!canSeek"
            :style="{ '--range-progress': `${progress}%` }"
            aria-label="Позиция воспроизведения"
            :aria-valuetext="`${formatTime(currentTime)} из ${formatTime(duration)}`"
            @input="seek"
          />

          <div class="music-card__times">
            <span>{{ formatTime(currentTime) }}</span>
            <span>{{ formatTime(duration) }}</span>
          </div>
        </div>
      </div>

      <div class="music-card__volume">
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          stroke-linecap="round"
          stroke-linejoin="round"
          aria-hidden="true"
        >
          <path d="M11 5 6 9H3v6h3l5 4z" />
          <path d="M15 8a6 6 0 0 1 0 8M18 5a10 10 0 0 1 0 14" />
        </svg>

        <input
          class="music-card__range music-card__range--volume"
          type="range"
          min="0"
          max="1"
          step="0.01"
          :value="volume"
          :style="{ '--range-progress': `${volume * 100}%` }"
          aria-label="Громкость"
          @input="changeVolume"
        />
      </div>

      <div v-if="playbackError" class="music-card__error" role="alert">
        <p>{{ playbackError }}</p>

        <button
          class="btn btn-secondary btn-small"
          type="button"
          :disabled="buffering"
          @click="startPlayback(true)"
        >
          {{ buffering ? 'Загружаем…' : 'Повторить' }}
        </button>
      </div>
    </template>

    <p v-else class="music-card__hint">
      Один трек, который расскажет о вас чуть больше.
    </p>

    <footer v-if="editable" class="music-card__footer">
      <div class="music-card__actions">
        <button
          class="btn btn-secondary btn-small"
          type="button"
          :disabled="busy"
          @click="pickFile"
        >
          {{
            uploading
              ? 'Загружаем…'
              : hasMusic
                ? 'Заменить трек'
                : 'Добавить трек'
          }}
        </button>

        <button
          v-if="hasMusic"
          class="music-card__delete"
          type="button"
          :disabled="busy"
          @click="onRemove"
        >
          {{ removing ? 'Удаляем…' : 'Удалить' }}
        </button>
      </div>

      <p class="music-card__hint">MP3 или WAV · один трек</p>

      <p
        v-if="metadataNotice"
        class="music-card__hint"
        role="status"
      >
        {{ metadataNotice }}
      </p>

      <input
        ref="fileInput"
        type="file"
        accept=".mp3,.wav,audio/mpeg,audio/mp3,audio/wav,audio/x-wav"
        aria-label="Выбрать музыку"
        hidden
        :disabled="busy"
        @change="onFileChange"
      />

      <p
        v-if="error"
        class="form-error music-card__message"
        role="alert"
      >
        {{ error }}
      </p>

      <p
        v-if="successMessage"
        class="form-info music-card__message"
        role="status"
      >
        {{ successMessage }}
      </p>
    </footer>
  </section>
</template>

<style scoped>
.music-card {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  gap: 20px;
  width: 100%;
  min-width: 0;
  margin: 0;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: var(--bg-card);
  color: var(--text);
}

.music-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 20px;
}

.music-card__heading {
  margin: 0;
  font-size: 14px;
  font-weight: 650;
  line-height: 1.4;
}

.music-card__badge {
  color: var(--muted);
  font-size: 11px;
}

.music-card__track {
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
}

.music-card__art {
  display: grid;
  flex: 0 0 66px;
  width: 66px;
  height: 66px;
  overflow: hidden;
  place-items: center;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-soft);
}

.music-card__art--empty {
  color: var(--accent);
}

.music-card__art > svg {
  width: 29px;
  height: 29px;
}

.music-card__cover {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.music-card__description {
  flex: 1;
  min-width: 0;
}

.music-card__title,
.music-card__artist {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.music-card__title {
  margin: 0;
  font-size: 14px;
  font-weight: 650;
  line-height: 1.5;
}

.music-card__artist {
  margin: 4px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}

.music-card__status {
  margin: 5px 0 0;
  color: var(--accent);
  font-size: 10px;
  line-height: 1.4;
}

.music-card__controls {
  display: flex;
  align-items: center;
  gap: 13px;
}

.music-card__play {
  display: grid;
  flex: 0 0 42px;
  width: 42px;
  height: 42px;
  padding: 0;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: var(--accent);
  color: var(--on-accent);
  cursor: pointer;
  transition: filter 0.15s ease, transform 0.15s ease;
}

.music-card__play:hover {
  filter: brightness(1.08);
}

.music-card__play:active {
  transform: scale(0.96);
}

.music-card__play svg {
  width: 22px;
  height: 22px;
}

.music-card__timeline {
  flex: 1;
  min-width: 0;
}

.music-card__range {
  --range-progress: 0%;
  display: block;
  box-sizing: border-box;
  width: 100%;
  height: 18px;
  margin: 0;
  padding: 0;
  appearance: none;
  -webkit-appearance: none;
  border: 0;
  border-radius: 0;
  background: transparent;
  cursor: pointer;
  accent-color: var(--accent);
}

.music-card__range::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 4px;
  background: linear-gradient(
    to right,
    var(--accent) 0%,
    var(--accent) var(--range-progress),
    var(--border) var(--range-progress),
    var(--border) 100%
  );
}

.music-card__range::-moz-range-track {
  height: 4px;
  border-radius: 4px;
  background: var(--border);
}

.music-card__range::-moz-range-progress {
  height: 4px;
  border-radius: 4px;
  background: var(--accent);
}

.music-card__range::-webkit-slider-thumb {
  width: 10px;
  height: 10px;
  margin-top: -3px;
  appearance: none;
  -webkit-appearance: none;
  border: 0;
  border-radius: 50%;
  background: var(--accent);
}

.music-card__range::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border: 0;
  border-radius: 50%;
  background: var(--accent);
}

.music-card__range:disabled {
  opacity: 0.45;
  cursor: default;
}

.music-card__times {
  display: flex;
  justify-content: space-between;
  color: var(--muted);
  font-size: 10px;
  font-variant-numeric: tabular-nums;
  line-height: 1.4;
}

.music-card__volume {
  display: flex;
  align-items: center;
  align-self: flex-end;
  gap: 9px;
  margin-top: -8px;
}

.music-card__volume svg {
  width: 15px;
  height: 15px;
  color: var(--muted);
}

.music-card__range--volume {
  width: 74px;
}

.music-card__footer {
  display: grid;
  gap: 12px;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.music-card__actions {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.music-card__delete {
  padding: 6px 0;
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.music-card__delete:hover:not(:disabled) {
  color: var(--text);
}

.music-card__delete:disabled {
  opacity: 0.5;
  cursor: default;
}

.music-card__hint {
  margin: 0;
  color: var(--muted);
  font-size: 11px;
  line-height: 1.65;
}

.music-card__error {
  display: grid;
  justify-items: start;
  gap: 10px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.music-card__error p {
  margin: 0;
  font-size: 12px;
  line-height: 1.65;
  overflow-wrap: anywhere;
}

.music-card__message {
  margin: 0;
  overflow-wrap: anywhere;
}

.music-card__equalizer {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 16px;
  color: var(--accent);
}

.music-card__equalizer span {
  width: 3px;
  height: 12px;
  border-radius: 3px;
  background: currentColor;
  animation: music-level 0.85s ease-in-out infinite alternate;
}

.music-card__equalizer span:nth-child(2) {
  animation-delay: -0.35s;
}

.music-card__equalizer span:nth-child(3) {
  animation-delay: -0.6s;
}

.music-card button:focus-visible,
.music-card input:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 4px;
}

@keyframes music-level {
  from {
    transform: scaleY(0.35);
  }
  to {
    transform: scaleY(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .music-card__equalizer span {
    animation: none;
  }

  .music-card__play {
    transition: none;
  }
}
</style>
