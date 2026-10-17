<script setup>
import { ref, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/AppShell.vue'
import UserCard from '@/components/UserCard.vue'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const user = ref(null)
const loading = ref(true)
const error = ref('')

async function load(username) {
  loading.value = true
  error.value = ''
  user.value = null
  try {
    const data = await auth.fetchUserByUsername(username)
    if (data.username === auth.user?.username) {
      router.replace({ name: 'me' })
      return
    }
    user.value = data
  } catch (e) {
    if (e?.status === 404) error.value = 'Пользователь не найден.'
    else if (e?.status === 0) error.value = 'Нет связи с сервером.'
    else error.value = 'Не удалось загрузить профиль.'
  } finally {
    loading.value = false
  }
}

onMounted(() => load(route.params.username))
watch(() => route.params.username, (u) => { if (u) load(u) })
</script>

<template>
  <AppShell>
    <div class="container">
      <section class="app-section">
        <p v-if="loading" class="app-hint">Загружаем…</p>
        <p v-else-if="error" class="form-error" role="alert">{{ error }}</p>
        <template v-else-if="user">
          <UserCard :user="user" />

          <div class="app-profile-actions" style="margin-top: 18px;">
            <RouterLink
              :to="{ name: 'chat', params: { userId: user.user_id } }"
              class="btn btn-primary"
            >
              Написать
            </RouterLink>
          </div>
        </template>
      </section>
    </div>
  </AppShell>
</template>