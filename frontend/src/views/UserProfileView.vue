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
        <div class="app-section--hero">
        <span class="eyebrow">
            <span class="status-dot"></span>
            Профиль
        </span>
        <h1 class="app-title app-title--hero">
            <span class="gradient-text">@{{ route.params.username }}</span>
        </h1>
        </div>
        <p v-if="loading" class="app-hint">Загружаем…</p>
        <p v-else-if="error" class="form-error" role="alert">{{ error }}</p>
        <UserCard v-else-if="user" :user="user" />
      </section>
    </div>
  </AppShell>
</template>