<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import AppShell from '@/components/AppShell.vue'
import UserCard from '@/components/UserCard.vue'
import ProfilePosts from '@/features/posts/components/ProfilePosts.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()

const user = ref(null)
const loading = ref(false)
const error = ref('')
let generation = 0

function prepareConversation() {
  if (!user.value) return

  chat.upsertConversation(user.value)
}

async function load(username) {
  const current = ++generation

  user.value = null
  error.value = ''
  loading.value = true

  try {
    if (!username) {
      error.value = 'Не указан пользователь.'
      return
    }

    const data = await auth.fetchUserByUsername(username)
    if (current !== generation) return

    if (data.username === auth.user?.username) {
      await router.replace({ name: 'me' })
      return
    }

    user.value = data

    // Если диалог уже существует, обновляем имя, ник и аватар.
    // Простое открытие профиля не создаёт новый диалог.
    const existingConversation = chat.conversations.find(
      (conversation) =>
        String(conversation.user_id) === String(data.user_id),
    )

    if (existingConversation) {
      chat.upsertConversation({
        ...data,
        user_id: existingConversation.user_id,
      })
    }
  } catch (cause) {
    if (current !== generation) return

    if (cause?.status === 404) {
      error.value = 'Пользователь не найден.'
    } else if (cause?.status === 0) {
      error.value = 'Нет связи с сервером.'
    } else if (cause?.status === 429) {
      error.value = 'Слишком много запросов. Попробуйте позже.'
    } else {
      error.value = 'Не удалось загрузить профиль.'
    }
  } finally {
    if (current === generation) loading.value = false
  }
}

watch(
  () => route.params.username,
  (username) => load(username),
  { immediate: true },
)

onBeforeUnmount(() => {
  generation += 1
})
</script>

<template>
  <AppShell>
    <div class="container">
      <p v-if="loading" class="public-profile__status" role="status">
        Загружаем профиль…
      </p>

      <div v-else-if="error" class="public-profile__status" role="alert">
        <p>{{ error }}</p>
        <button
          class="btn btn-secondary btn-small"
          type="button"
          @click="load(route.params.username)"
        >
          Повторить
        </button>
      </div>

      <template v-else-if="user">
        <section class="app-section">
          <div class="app-profile-row">
            <div class="app-profile-avatar">
              <UserAvatar :user="user" :size="128" />
            </div>

            <div class="app-profile-info">
              <UserCard :user="user" hide-avatar />

              <div class="app-profile-actions">
                <RouterLink
                :to="{ name: 'chat', params: { userId: user.user_id } }"
                class="btn btn-primary"
                @click="prepareConversation"
              >
                Написать сообщение
              </RouterLink>
              </div>
            </div>
          </div>
        </section>

        <ProfilePosts :key="user.username" :username="user.username" />
      </template>
    </div>
  </AppShell>
</template>

<style scoped>
.public-profile {
  min-width: 0;
}

.public-profile__actions {
  display: flex;
  gap: 10px;
  margin-top: 14px;
}

.public-profile__status {
  margin: 0;
  padding: 16px 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}
</style>
