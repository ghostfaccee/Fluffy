<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  STORY_ACCEPT,
  STORY_TITLE_LIMIT,
  createStory,
  getStoryContentType,
  storyErrorMessage,
  uploadStoryMedia,
} from '@/modules/stories/api/stories'

const emit = defineEmits(['close', 'created'])

const dialog = ref(null)
const fileInput = ref(null)
const title = ref('')
const file = ref(null)
const previewUrl = ref('')
const error = ref('')
const phase = ref('idle')
const uploadedKey = ref('')
const uncertainResult = ref(false)

let disposed = false
let controller = null

const busy = computed(() => phase.value !== 'idle')

const normalizedTitle = computed(() => title.value.trim())

const titleLength = computed(
  () => Array.from(normalizedTitle.value).length,
)

const isVideo = computed(() =>
  Boolean(file.value && getStoryContentType(file.value)?.startsWith('video/')),
)

const canSubmit = computed(
  () =>
    !busy.value &&
    Boolean(file.value) &&
    titleLength.value > 0 &&
    titleLength.value <= STORY_TITLE_LIMIT,
)

const submitLabel = computed(() => {
  if (phase.value === 'uploading') return 'Загружаем файл…'
  if (phase.value === 'publishing') return 'Публикуем…'

  return 'Опубликовать'
})

function clearPreview() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = ''
  }
}

function onFileChange(event) {
  const selected = event.target.files?.[0]

  event.target.value = ''

  if (!selected || busy.value) return

  error.value = ''
  uncertainResult.value = false

  if (!getStoryContentType(selected)) {
    error.value = 'Поддерживаются только JPEG, PNG, MP4 и MPEG.'
    return
  }

  if (selected.size === 0) {
    error.value = 'Выбранный файл пуст.'
    return
  }

  clearPreview()

  file.value = selected
  uploadedKey.value = ''
  previewUrl.value = URL.createObjectURL(selected)
}

function requestClose() {
  if (busy.value) return

  emit('close')
}

function onCancel(event) {
  event.preventDefault()
  requestClose()
}

async function submit() {
  if (!canSubmit.value) return

  error.value = ''
  uncertainResult.value = false
  controller = new AbortController()

  try {
    if (!uploadedKey.value) {
      phase.value = 'uploading'

      uploadedKey.value = await uploadStoryMedia(file.value, {
        signal: controller.signal,
        isCurrent: () => !disposed,
      })
    }

    if (disposed) return

    phase.value = 'publishing'

    const story = await createStory({
      title: normalizedTitle.value,
      mediaKey: uploadedKey.value,
    })

    if (disposed) return

    emit('created', story)
  } catch (cause) {
    if (disposed) return

    error.value = storyErrorMessage(cause)

    // Сетевая ошибка во время POST не доказывает, что сервер
    // не успел создать историю. Автоматически POST не повторяем.
    uncertainResult.value =
      phase.value === 'publishing' &&
      (cause?.status === 0 || cause instanceof TypeError)
  } finally {
    if (!disposed) {
      phase.value = 'idle'
    }
  }
}

onMounted(() => {
  dialog.value?.showModal()
})

onBeforeUnmount(() => {
  disposed = true
  controller?.abort()
  clearPreview()
  dialog.value?.close()
})
</script>

<template>
  <dialog
    ref="dialog"
    class="story-composer"
    aria-labelledby="story-composer-title"
    @cancel="onCancel"
  >
    <form class="story-composer__form" @submit.prevent="submit">
      <header class="story-composer__header">
        <div>
          <h2 id="story-composer-title">Новая история</h2>
          <p>Изображение или видео для вашего профиля.</p>
        </div>

        <button
          class="btn btn-secondary btn-small"
          type="button"
          aria-label="Закрыть создание истории"
          :disabled="busy"
          @click="requestClose"
        >
          Закрыть
        </button>
      </header>

      <div class="field">
        <label for="story-title">Заголовок</label>

        <input
          id="story-title"
          v-model="title"
          type="text"
          autocomplete="off"
          required
          :disabled="busy"
          :aria-invalid="titleLength > STORY_TITLE_LIMIT"
          aria-describedby="story-title-hint"
        />

        <span
          id="story-title-hint"
          class="story-composer__hint"
          :class="{ 'story-composer__hint--error': titleLength > STORY_TITLE_LIMIT }"
        >
          {{ titleLength }} / {{ STORY_TITLE_LIMIT }}
        </span>
      </div>

      <div class="story-composer__file">
        <input
          id="story-media"
          ref="fileInput"
          class="story-composer__input"
          type="file"
          :accept="STORY_ACCEPT"
          :disabled="busy"
          @change="onFileChange"
        />

        <button
          class="btn btn-secondary"
          type="button"
          :disabled="busy"
          @click="fileInput?.click()"
        >
          {{ file ? 'Выбрать другой файл' : 'Выбрать фото или видео' }}
        </button>

        <p v-if="file" class="story-composer__filename">
          {{ file.name }}
        </p>

        <p class="story-composer__hint">
          JPEG, PNG, MP4 или MPEG. Воспроизведение MPEG зависит от браузера.
        </p>
      </div>

      <div v-if="previewUrl" class="story-composer__preview">
        <video
          v-if="isVideo"
          :src="previewUrl"
          controls
          playsinline
          preload="metadata"
        />

        <img
          v-else
          :src="previewUrl"
          alt="Предпросмотр новой истории"
        />
      </div>

      <p v-if="error" class="form-error" role="alert">
        {{ error }}
      </p>

      <p v-if="uncertainResult" class="form-info" role="status">
        Сервер мог успеть создать историю до обрыва соединения.
        Перед повторной публикацией закройте окно и обновите список историй,
        чтобы не создать дубликат.
      </p>

      <footer class="story-composer__footer">
        <button
          class="btn btn-secondary"
          type="button"
          :disabled="busy"
          @click="requestClose"
        >
          Отмена
        </button>

        <button
          class="btn btn-primary"
          type="submit"
          :disabled="!canSubmit"
        >
          {{ submitLabel }}
        </button>
      </footer>

      <p v-if="busy" class="story-composer__hint" role="status">
        Не закрывайте страницу до завершения публикации.
      </p>
    </form>
  </dialog>
</template>

<style scoped>
.story-composer {
  width: min(560px, calc(100vw - 32px));
  max-height: calc(100dvh - 32px);
  margin: auto;
  padding: 0;
  overflow: auto;
  color: var(--text);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 20px;
}

.story-composer::backdrop {
  background: rgb(0 0 0 / 72%);
}

.story-composer__form {
  display: grid;
  gap: 20px;
  padding: 24px;
}

.story-composer__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.story-composer__header h2 {
  margin: 0;
  font-size: 20px;
}

.story-composer__header p,
.story-composer__hint,
.story-composer__filename {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.story-composer__filename {
  overflow-wrap: anywhere;
}

.story-composer__hint--error {
  color: #e57373;
}

.story-composer__input {
  display: none;
}

.story-composer__preview {
  display: grid;
  place-items: center;
  overflow: hidden;
  background: #111318;
  border-radius: 14px;
}

.story-composer__preview img,
.story-composer__preview video {
  display: block;
  width: 100%;
  max-height: 380px;
  object-fit: contain;
}

.story-composer__footer {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
}

@media (max-width: 600px) {
  .story-composer__form {
    padding: 18px;
  }

  .story-composer__header {
    flex-wrap: wrap;
  }
}
</style>
