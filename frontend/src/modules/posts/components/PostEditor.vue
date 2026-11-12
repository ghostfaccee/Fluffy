<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { postsApi } from '../api/posts'

const props = defineProps({
  post: {
    type: Object,
    default: null,
  },
})

const emit = defineEmits(['saved', 'cancel'])

const form = reactive({ title: '', content: '' })
const initial = reactive({ title: '', content: '' })
const pending = ref(false)
const error = ref('')

const editing = computed(() => Boolean(props.post?.post_id))
const dirty = computed(
  () => form.title !== initial.title || form.content !== initial.content,
)
const valid = computed(
  () =>
    form.title.trim().length > 0 &&
    form.title.length <= 200 &&
    form.content.trim().length > 0 &&
    form.content.length <= 4096,
)

watch(
  () => props.post,
  (post) => {
    form.title = post?.title ?? ''
    form.content = post?.content ?? ''
    initial.title = form.title
    initial.content = form.content
    error.value = ''
  },
  { immediate: true },
)

function errorMessage(cause) {
  if (cause.status === 429) {
    return 'Слишком много запросов. Подождите немного перед повторной отправкой.'
  }

  if (cause.status === 403) {
    return 'Недостаточно прав для изменения этой публикации.'
  }

  if (cause.status === 404) {
    return 'Публикация не найдена. Возможно, она уже удалена.'
  }

  if (Array.isArray(cause.detail)) {
    return cause.detail.map((item) => item.msg).filter(Boolean).join('. ')
      || 'Проверьте заполненные поля.'
  }

  return typeof cause.detail === 'string'
    ? cause.detail
    : cause.message || 'Не удалось сохранить публикацию.'
}

async function submit() {
  if (pending.value || !valid.value) return
  if (editing.value && !dirty.value) return

  pending.value = true
  error.value = ''

  try {
    const data = {
      title: form.title,
      content: form.content,
    }

    const saved = editing.value
      ? await postsApi.update(props.post.post_id, data)
      : await postsApi.create(data)

    form.title = editing.value ? saved.title : ''
    form.content = editing.value ? saved.content : ''
    initial.title = form.title
    initial.content = form.content

    emit('saved', saved)
  } catch (cause) {
    error.value = errorMessage(cause)
  } finally {
    pending.value = false
  }
}

function cancel() {
  if (pending.value) return
  if (dirty.value && !window.confirm('Отменить несохранённые изменения?')) return
  emit('cancel')
}

function beforeUnload(event) {
  if (!dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}

window.addEventListener('beforeunload', beforeUnload)

onBeforeUnmount(() => {
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

    <fieldset :disabled="pending">
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
        :disabled="pending || !valid || (editing && !dirty)"
      >
        {{ pending ? 'Сохраняем…' : editing ? 'Сохранить' : 'Опубликовать' }}
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
  font-size: 14px;
  opacity: 0.65;
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
  transition: border-color 150ms, background 150ms;
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
  outline: 2px solid var(--fluffy-accent, currentColor);
  outline-offset: 3px;
}

.post-editor__field small {
  justify-self: end;
  font-size: 12px;
  font-weight: 400;
  opacity: 0.55;
}

.post-editor__error {
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
  border-top: 1px solid color-mix(in srgb, currentColor 10%, transparent);
}

.post-editor__button {
  min-height: 42px;
  padding: 10px 18px;
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

.post-editor__button:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

@media (max-width: 480px) {
  .post-editor__badge {
    display: none;
  }

  .post-editor__footer {
    display: grid;
    grid-template-columns: 1fr 1fr;
  }
}
</style>
