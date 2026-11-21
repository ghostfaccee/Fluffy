<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import PostMedia from './PostMedia.vue'
import {
  POST_MEDIA_ACCEPT,
  getPostMediaType,
  postsApi,
  validatePostMedia,
} from '../api/posts'

const props = defineProps({
  post: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['saved', 'cancel'])

const form = reactive({ title: '', content: '' })
const initial = reactive({ title: '', content: '' })

const picker = ref(null)
const phase = ref('idle')
const error = ref('')
const fileError = ref('')
const file = ref(null)
const previewUrl = ref('')
const uploadedKey = ref(undefined)
const removePublishedMedia = ref(false)
const uncertainResult = ref(false)

let submission = null

const editing = computed(() => Boolean(props.post?.post_id))
const hasPublishedMedia = computed(() => Boolean(props.post?.media_url))
const pending = computed(() => phase.value !== 'idle')
const locked = computed(() => pending.value || uncertainResult.value)
const previewIsVideo = computed(
  () => getPostMediaType(file.value)?.startsWith('video/') ?? false,
)

const dirty = computed(
  () =>
    form.title !== initial.title ||
    form.content !== initial.content ||
    file.value !== null ||
    removePublishedMedia.value,
)

const valid = computed(
  () =>
    form.title.trim().length > 0 &&
    form.title.length <= 200 &&
    form.content.trim().length > 0 &&
    form.content.length <= 4096,
)

const submitLabel = computed(() => {
  if (phase.value === 'uploading') return 'Загружаем файл…'
  if (phase.value === 'saving') {
    return editing.value ? 'Сохраняем…' : 'Публикуем…'
  }
  return editing.value ? 'Сохранить' : 'Опубликовать'
})

function clearFile() {
  if (previewUrl.value) URL.revokeObjectURL(previewUrl.value)

  previewUrl.value = ''
  file.value = null
  uploadedKey.value = undefined
  fileError.value = ''
}

function openPicker() {
  if (locked.value || hasPublishedMedia.value) return
  picker.value?.click()
}

function onFileChange(event) {
  const selected = event.target.files?.[0]
  event.target.value = ''

  if (!selected || locked.value || hasPublishedMedia.value) return

  try {
    validatePostMedia(selected)
  } catch (cause) {
    fileError.value = file.value
      ? `${cause.message} Предыдущее вложение оставлено.`
      : cause.message
    return
  }

  clearFile()
  error.value = ''
  file.value = selected
  previewUrl.value = URL.createObjectURL(selected)
}

function removeAttachment() {
  if (locked.value) return

  error.value = ''

  if (hasPublishedMedia.value) {
    removePublishedMedia.value = true
  } else {
    clearFile()
  }
}

function undoRemoval() {
  if (locked.value) return

  removePublishedMedia.value = false
  error.value = ''
}

watch(
  () => props.post,
  (post) => {
    submission?.abort()
    submission = null
    phase.value = 'idle'
    error.value = ''
    uncertainResult.value = false
    removePublishedMedia.value = false
    clearFile()

    form.title = post?.title ?? ''
    form.content = post?.content ?? ''
    initial.title = form.title
    initial.content = form.content
  },
  { immediate: true },
)

function errorMessage(cause) {
  if (cause?.status === 429) {
    return 'Слишком много запросов. Подождите немного перед повторной отправкой.'
  }

  if (cause?.status === 403) {
    return 'Недостаточно прав для этого действия.'
  }

  if (cause?.status === 404) {
    return 'Публикация не найдена. Возможно, она уже удалена.'
  }

  if (Array.isArray(cause?.detail)) {
    return (
      cause.detail.map((item) => item.msg).filter(Boolean).join('. ') ||
      'Проверьте заполненные поля.'
    )
  }

  return typeof cause?.detail === 'string'
    ? cause.detail
    : cause?.message || 'Не удалось сохранить публикацию.'
}

async function submit() {
  if (locked.value || !valid.value) return
  if (editing.value && !dirty.value) return

  const controller = new AbortController()
  const { signal } = controller
  const postId = props.post?.post_id
  const selectedFile = file.value
  const data = { title: form.title, content: form.content }

  submission = controller
  error.value = ''

  try {
    if (postId && hasPublishedMedia.value && removePublishedMedia.value) {
      // postsApi передаст именно media_key: null, а не пропустит поле.
      data.mediaKey = null
    } else if (selectedFile && !hasPublishedMedia.value) {
      if (uploadedKey.value === undefined) {
        phase.value = 'uploading'

        const key = await postsApi.uploadMedia(selectedFile, { signal })
        if (signal.aborted) return

        uploadedKey.value = key
      }

      data.mediaKey = uploadedKey.value
    }

    if (signal.aborted) return

    phase.value = 'saving'

    const saved = postId
      ? await postsApi.update(postId, data)
      : await postsApi.create(data)

    if (signal.aborted) return

    form.title = postId ? saved.title : ''
    form.content = postId ? saved.content : ''
    initial.title = form.title
    initial.content = form.content
    removePublishedMedia.value = false
    clearFile()

    emit('saved', saved)
  } catch (cause) {
    if (signal.aborted) return

    if (
      phase.value === 'saving' &&
      (cause?.status === 0 ||
        cause?.status >= 500 ||
        cause instanceof TypeError ||
        cause instanceof SyntaxError)
    ) {
      uncertainResult.value = true
      error.value =
        'Не удалось подтвердить сохранение. Сервер мог уже принять изменения. ' +
        'Закройте редактор и обновите страницу, чтобы проверить публикацию.'
    } else {
      error.value = errorMessage(cause)
    }
  } finally {
    if (submission === controller) {
      submission = null
      phase.value = 'idle'
    }
  }
}

function cancel() {
  if (pending.value) return
  if (dirty.value && !window.confirm('Отменить несохранённые изменения?')) return
  emit('cancel')
}

function beforeUnload(event) {
  if (!dirty.value && !pending.value) return

  event.preventDefault()
  event.returnValue = ''
}

window.addEventListener('beforeunload', beforeUnload)

onBeforeUnmount(() => {
  submission?.abort()
  clearFile()
  window.removeEventListener('beforeunload', beforeUnload)
})
</script>

<template>
  <form class="post-editor" :aria-busy="pending" @submit.prevent="submit">
    <header class="post-editor__header">
      <div>
        <h2>{{ editing ? 'Редактирование публикации' : 'Новая публикация' }}</h2>
        <p>Поделитесь тем, что для вас важно.</p>
      </div>
      <span class="post-editor__badge">Публикация</span>
    </header>

    <fieldset :disabled="locked">
      <label class="post-editor__field">
        <span>Заголовок</span>
        <input
          v-model="form.title"
          name="title"
          type="text"
          maxlength="200"
          placeholder="О чём хотите рассказать?"
          required
        />
        <small>{{ form.title.length }} / 200</small>
      </label>

      <label class="post-editor__field">
        <span>Текст публикации</span>
        <textarea
          v-model="form.content"
          name="content"
          maxlength="4096"
          placeholder="Ваши мысли, новости или небольшая история…"
          rows="7"
          required
        />
        <small>{{ form.content.length }} / 4096</small>
      </label>

      <div class="post-editor__attachment">
        <p class="post-editor__attachment-label">
          Вложение
          <span v-if="!hasPublishedMedia" class="post-editor__hint">
            · необязательно
          </span>
        </p>

        <input
          v-if="!hasPublishedMedia"
          ref="picker"
          type="file"
          name="media"
          :accept="POST_MEDIA_ACCEPT"
          hidden
          @change="onFileChange"
        />

        <div v-if="removePublishedMedia" class="post-editor__removal">
          <p role="status">Вложение будет удалено после сохранения.</p>
          <button
            class="post-editor__button post-editor__button--secondary"
            type="button"
            @click="undoRemoval"
          >
            Отменить удаление
          </button>
        </div>

        <template v-else-if="hasPublishedMedia || file">
          <div class="post-editor__media-frame">
            <PostMedia
              v-if="hasPublishedMedia"
              class="post-editor__published-media"
              :post="post"
            />

            <video
              v-else-if="previewIsVideo"
              :key="`preview-video:${previewUrl}`"
              class="post-editor__preview post-editor__preview--video"
              :src="previewUrl"
              controls
              playsinline
              preload="metadata"
              aria-label="Предпросмотр видео"
            />

            <img
              v-else
              :key="`preview-image:${previewUrl}`"
              class="post-editor__preview"
              :src="previewUrl"
              alt="Предпросмотр изображения"
            />

            <button
              class="post-editor__remove"
              type="button"
              :aria-label="hasPublishedMedia ? 'Удалить вложение из поста' : 'Убрать выбранный файл'"
              :title="hasPublishedMedia ? 'Удалить вложение из поста' : 'Убрать выбранный файл'"
              @click="removeAttachment"
            >
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden="true"
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

          <div v-if="file" class="post-editor__file-row">
            <span>{{ file.name }}</span>
            <button
              class="post-editor__button post-editor__button--secondary"
              type="button"
              @click="openPicker"
            >
              Выбрать другой файл
            </button>
          </div>
        </template>

        <button
          v-else
          class="post-editor__picker"
          type="button"
          @click="openPicker"
        >
          <span class="post-editor__picker-icon" aria-hidden="true">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <rect
                x="3"
                y="4"
                width="18"
                height="16"
                rx="3"
                stroke="currentColor"
                stroke-width="1.7"
              />
              <circle cx="8.5" cy="9" r="1.4" fill="currentColor" />
              <path
                d="m4 17 4-4 3 3 4.5-5 4.5 5"
                stroke="currentColor"
                stroke-width="1.7"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </span>

          <span class="post-editor__picker-copy">
            <strong>Добавить фото или видео</strong>
            <span>Один файл · JPEG, PNG, MP4 или MPEG</span>
          </span>

          <svg
            class="post-editor__picker-plus"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <path
              d="M12 5v14M5 12h14"
              stroke="currentColor"
              stroke-width="2"
              stroke-linecap="round"
            />
          </svg>
        </button>

        <p v-if="fileError" class="post-editor__error" role="alert">
          {{ fileError }}
        </p>
      </div>
    </fieldset>

    <p v-if="error" class="post-editor__error" role="alert">
      {{ error }}
    </p>

    <footer class="post-editor__footer">
      <button
        class="post-editor__button post-editor__button--secondary"
        type="button"
        :disabled="pending"
        @click="cancel"
      >
        Отмена
      </button>

      <button
        class="post-editor__button post-editor__button--primary"
        type="submit"
        :disabled="locked || !valid || (editing && !dirty)"
      >
        {{ submitLabel }}
      </button>
    </footer>
  </form>
</template>

<style scoped>
.post-editor {
  color: inherit;
  font: inherit;
}

.post-editor__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.post-editor__header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 650;
  letter-spacing: -0.025em;
}

.post-editor__header p {
  margin: 7px 0 0;
  color: var(--muted);
  font-size: 14px;
}

.post-editor__badge {
  padding: 6px 10px;
  border-radius: 999px;
  background: color-mix(in srgb, currentColor 6%, transparent);
  font-size: 12px;
}

.post-editor fieldset {
  display: grid;
  gap: 20px;
  min-width: 0;
  margin: 0;
  padding: 0;
  border: 0;
}

.post-editor__field {
  display: grid;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
}

.post-editor__field input,
.post-editor__field textarea {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  padding: 13px 15px;
  border: 1px solid color-mix(in srgb, currentColor 16%, transparent);
  border-radius: 12px;
  background: color-mix(in srgb, currentColor 3%, transparent);
  color: inherit;
  font: inherit;
  line-height: 1.6;
}

.post-editor__field textarea {
  min-height: 180px;
  resize: vertical;
}

.post-editor__field input::placeholder,
.post-editor__field textarea::placeholder {
  color: inherit;
  opacity: 0.45;
}

.post-editor :is(input, textarea, button):focus-visible {
  outline: 2px solid var(--accent, var(--fluffy-accent, currentColor));
  outline-offset: 3px;
}

.post-editor__field small {
  justify-self: end;
  color: var(--muted);
  font-size: 12px;
  font-weight: 400;
}

.post-editor__attachment {
  display: grid;
  gap: 10px;
  min-width: 0;
}

.post-editor__attachment-label {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.post-editor__hint {
  color: var(--muted);
  font-size: 12px;
  font-weight: 400;
}

.post-editor__picker {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  min-width: 0;
  padding: 12px;
  border: 1px dashed var(--border);
  border-radius: 12px;
  background: color-mix(in srgb, currentColor 3%, transparent);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.post-editor__picker:hover:not(:disabled) {
  border-color: var(--accent, var(--fluffy-accent, currentColor));
}

.post-editor__picker-icon {
  display: grid;
  flex: 0 0 40px;
  height: 40px;
  place-items: center;
  border-radius: 10px;
  background: color-mix(
    in srgb,
    var(--accent, var(--fluffy-accent, currentColor)) 14%,
    transparent
  );
  color: var(--accent, var(--fluffy-accent, currentColor));
}

.post-editor__picker-copy {
  display: grid;
  flex: 1 1 auto;
  gap: 3px;
  min-width: 0;
  overflow-wrap: anywhere;
}

.post-editor__picker-copy strong {
  font-size: 14px;
  font-weight: 600;
}

.post-editor__picker-copy > span {
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
}

.post-editor__picker-plus {
  flex: 0 0 auto;
  color: var(--muted);
}

.post-editor__media-frame {
  position: relative;
  width: min(100%, 440px);
  min-width: 0;
}

.post-editor__published-media {
  --post-media-width: 100%;
  --post-media-image-height: min(280px, 42vh);
  --post-media-video-height: min(280px, 42vh);
}

.post-editor__preview {
  display: block;
  box-sizing: border-box;
  width: 100%;
  height: auto;
  max-height: min(280px, 42vh);
  border: 1px solid var(--border);
  border-radius: 12px;
  background: color-mix(in srgb, currentColor 5%, transparent);
  object-fit: contain;
}

.post-editor__preview--video {
  aspect-ratio: 16 / 9;
  background: #111318;
}

.post-editor__remove {
  position: absolute;
  z-index: 1;
  top: 8px;
  right: 8px;
  display: grid;
  width: 44px;
  height: 44px;
  padding: 0;
  place-items: center;
  border: 1px solid rgb(255 255 255 / 25%);
  border-radius: 50%;
  background: rgb(0 0 0 / 75%);
  color: #fff;
  cursor: pointer;
}

.post-editor__remove:hover:not(:disabled) {
  background: #942e3b;
}

.post-editor__removal {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 12px;
}

.post-editor__removal p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.post-editor__file-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  color: var(--muted);
  font-size: 13px;
  overflow-wrap: anywhere;
}

.post-editor__file-row span {
  min-width: 0;
}

.post-editor__error {
  margin: 10px 0 0;
  padding: 12px 14px;
  border: 1px solid currentColor;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.5;
}

.post-editor__footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}

.post-editor__button {
  min-height: 42px;
  padding: 10px 14px;
  border: 1px solid transparent;
  border-radius: 10px;
  font: inherit;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.post-editor__button--primary {
  background: var(--fluffy-accent, CanvasText);
  color: var(--fluffy-on-accent, Canvas);
}

.post-editor__button--secondary {
  background: color-mix(in srgb, currentColor 6%, transparent);
  color: inherit;
}

.post-editor button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .post-editor__badge,
  .post-editor__picker-plus {
    display: none;
  }

  .post-editor__footer {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
</style>
