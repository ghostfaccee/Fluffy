<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useAuthStore } from '@/modules/auth/stores/auth'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import PostEditor from './PostEditor.vue'
import { postsApi } from '../api/posts'

const props = defineProps({
  username: {
    type: String,
    required: true,
  },
})

const auth = useAuthStore()
const posts = ref([])
const loading = ref(false)
const deleting = ref(null)
const error = ref('')
const hasMore = ref(false)
const offset = ref(0)
const editorOpen = ref(false)
const editedPost = ref(null)

const pageSize = 20
let generation = 0

const ownProfile = computed(
  () => props.username === auth.user?.username,
)

const dateFormatter = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
})

function formatDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? '' : dateFormatter.format(date)
}

function message(cause) {
  if (cause?.status === 429) return 'Слишком много запросов. Попробуйте немного позже.'
  if (cause?.status === 0) return 'Нет связи с сервером.'
  if (cause?.status === 403) return 'Недостаточно прав для этого действия.'
  if (cause?.status === 404) return 'Пользователь или публикация не найдены.'
  return 'Не удалось выполнить действие. Попробуйте ещё раз.'
}

async function load(reset = false) {
  if (loading.value && !reset) return

  const current = ++generation
  const username = props.username

  if (reset) {
    posts.value = []
    offset.value = 0
    hasMore.value = false
  }

  if (!username) {
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''

  try {
    const batch = await postsApi.listByUser(username, {
      limit: pageSize,
      offset: offset.value,
    })

    if (current !== generation) return
    if (!Array.isArray(batch)) throw new Error('Unexpected response')

    const existing = new Set(posts.value.map((post) => post.post_id))
    posts.value.push(...batch.filter((post) => !existing.has(post.post_id)))
    offset.value += batch.length
    hasMore.value = batch.length === pageSize
  } catch (cause) {
    if (current === generation) error.value = message(cause)
  } finally {
    if (current === generation) loading.value = false
  }
}

function openEditor(post = null) {
  if (loading.value || deleting.value) return
  editedPost.value = post
  editorOpen.value = true
}

function closeEditor() {
  editorOpen.value = false
  editedPost.value = null
}

function onSaved(post) {
  const wasEditing = Boolean(editedPost.value)
  closeEditor()

  if (wasEditing) {
    posts.value = posts.value.map((item) =>
      item.post_id === post.post_id ? post : item,
    )
    return
  }

  load(true)
}

async function removePost(post) {
  if (deleting.value || loading.value || editorOpen.value) return
  if (!window.confirm(`Удалить публикацию «${post.title}»?`)) return

  const current = generation
  deleting.value = post.post_id
  error.value = ''

  try {
    await postsApi.remove(post.post_id)
    if (current !== generation) return
    await load(true)
  } catch (cause) {
    if (current === generation) error.value = message(cause)
  } finally {
    if (deleting.value === post.post_id) deleting.value = null
  }
}

watch(
  () => props.username,
  () => {
    closeEditor()
    deleting.value = null
    load(true)
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  generation += 1
})
</script>

<template>
  <section class="profile-posts" aria-label="Публикации пользователя">
    <header class="profile-posts__heading">
      <h2>Публикации</h2>
      <button
        v-if="ownProfile && !editorOpen"
        class="pp-button pp-button--primary"
        type="button"
        :disabled="loading || Boolean(deleting)"
        @click="openEditor()"
      >
        Написать пост
      </button>
    </header>

    <div v-if="editorOpen" class="pp-card pp-editor">
      <PostEditor
        :key="editedPost?.post_id || 'new'"
        :post="editedPost"
        @saved="onSaved"
        @cancel="closeEditor"
      />
    </div>

    <div v-if="error" class="pp-status" role="alert">
      <p>{{ error }}</p>
      <button
        class="pp-button"
        type="button"
        :disabled="loading || Boolean(deleting)"
        @click="load(posts.length === 0)"
      >
        Повторить загрузку
      </button>
    </div>

    <article v-for="post in posts" :key="post.post_id" class="pp-card">
      <header class="pp-author">
        <UserAvatar :user="post.author" :size="38" />

        <div class="pp-author__info">
          <RouterLink
            :to="post.author.username === auth.user?.username
              ? { name: 'me' }
              : { name: 'user', params: { username: post.author.username } }"
          >
            {{ post.author.name || post.author.username }}
          </RouterLink>
          <time :datetime="post.created_at">{{ formatDate(post.created_at) }}</time>
        </div>
      </header>

      <h3 class="pp-title">{{ post.title }}</h3>
      <p class="pp-content">{{ post.content }}</p>

      <footer v-if="ownProfile" class="pp-actions">
        <button
          class="pp-action"
          type="button"
          :disabled="loading || Boolean(deleting) || editorOpen"
          @click="openEditor(post)"
        >
          Редактировать
        </button>
        <button
          class="pp-action"
          type="button"
          :disabled="loading || Boolean(deleting) || editorOpen"
          @click="removePost(post)"
        >
          {{ deleting === post.post_id ? 'Удаляем…' : 'Удалить' }}
        </button>
      </footer>
    </article>

    <p v-if="loading" class="pp-empty" role="status">Загружаем публикации…</p>

    <p
      v-else-if="!posts.length && !error && !editorOpen"
      class="pp-empty"
    >
      {{ ownProfile
        ? 'Здесь будут ваши публикации. Начните с первой.'
        : 'Пользователь пока ничего не опубликовал.' }}
    </p>

    <button
      v-if="hasMore && !error"
      class="pp-button pp-more"
      type="button"
      :disabled="loading || Boolean(deleting) || editorOpen"
      @click="load()"
    >
      {{ loading ? 'Загружаем…' : 'Показать ещё' }}
    </button>
  </section>
</template>

<style scoped>
.profile-posts {
  --fluffy-accent: var(--green, #42c99a);
  --fluffy-on-accent: #10241e;
  display: grid;
  gap: 14px;
  min-width: 0;
  margin-top: 24px;
}

.profile-posts__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.profile-posts__heading h2 {
  margin: 0;
  color: var(--text);
  font-size: 18px;
  font-weight: 650;
  letter-spacing: -0.4px;
}

.pp-card {
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-card);
  color: var(--text);
}

.pp-author {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pp-author__info {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.pp-author__info a {
  color: var(--text);
  font-size: 13px;
  font-weight: 600;
  overflow-wrap: anywhere;
}

.pp-author__info time {
  color: var(--muted);
  font-size: 11px;
}

.pp-title {
  margin: 17px 0 8px;
  font-size: 17px;
  font-weight: 650;
  line-height: 1.4;
  letter-spacing: -0.3px;
  overflow-wrap: anywhere;
}

.pp-content {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.pp-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 18px;
  padding-top: 14px;
  margin-top: 18px;
  border-top: 1px solid var(--border);
}

.pp-action {
  padding: 4px 0;
  border: 0;
  background: transparent;
  color: var(--muted);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.pp-action:hover {
  color: var(--text);
}

.pp-button {
  min-height: 36px;
  padding: 8px 13px;
  border: 1px solid var(--border);
  border-radius: 9px;
  background: var(--bg-card);
  color: var(--text);
  font: inherit;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.pp-button--primary {
  border-color: transparent;
  background: var(--fluffy-accent);
  color: var(--fluffy-on-accent);
}

.pp-more {
  justify-self: center;
}

.pp-empty,
.pp-status {
  margin: 0;
  padding: 18px 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.pp-status p {
  margin: 0 0 10px;
}

.profile-posts button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.profile-posts :is(button, a):focus-visible {
  outline: 2px solid var(--fluffy-accent);
  outline-offset: 4px;
}

@media (max-width: 480px) {
  .pp-card {
    padding: 16px;
  }

  .profile-posts__heading h2 {
    font-size: 17px;
  }
}
</style>
