<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { useChatStore } from '@/modules/chat/stores/chat'
import AppShell from '@/app/layouts/AppShell.vue'
import UserCard from '@/modules/profile/components/UserCard.vue'
import ProfileMusic from '@/modules/profile/components/ProfileMusic.vue'
import ProfilePosts from '@/modules/posts/components/ProfilePosts.vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'

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

    // Открытие профиля не должно создавать новый диалог.
    // Уже существующему диалогу обновляем данные пользователя.
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
    if (current === generation) {
      loading.value = false
    }
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
        <div
          class="profile-overview"
          :class="{ 'profile-overview--with-music': user.music_url }"
        >
          <section class="app-section profile-overview__main">
            <div class="app-profile-row">
              <div class="app-profile-avatar">
                <UserAvatar :user="user" :size="128" />
              </div>

              <div class="app-profile-info">
                <UserCard :user="user" hide-avatar />

                <div class="app-profile-actions">
                  <RouterLink
                    :to="{
                      name: 'chat',
                      params: { userId: user.user_id },
                    }"
                    class="btn btn-primary"
                    @click="prepareConversation"
                  >
                    Написать сообщение
                  </RouterLink>
                </div>
              </div>
            </div>
          </section>

          <aside
            v-if="user.music_url"
            class="profile-overview__side"
            aria-label="Музыка"
          >
            <ProfileMusic
              :key="user.user_id"
              :music-url="user.music_url"
            />
          </aside>
        </div>

        <ProfilePosts :key="user.username" :username="user.username" />
      </template>
    </div>
  </AppShell>
</template>

<style scoped>
.profile-overview {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  align-items: start;
  gap: 20px;
  margin-bottom: 24px;
}

.profile-overview--with-music {
  grid-template-columns: minmax(0, 1fr) 290px;
}

.profile-overview__main {
  min-width: 0;
  margin: 0;
}

.profile-overview__main .app-profile-info {
  min-width: 0;
  overflow-wrap: anywhere;
}

.profile-overview__side {
  min-width: 0;
}

.public-profile__status {
  margin: 0;
  padding: 16px 0;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .profile-overview--with-music {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
