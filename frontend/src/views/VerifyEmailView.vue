<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { api } from '@/api/client'
import AuthShell from '@/components/AuthShell.vue'

const route = useRoute()
const router = useRouter()

const status = ref('loading')
const message = ref('')

onMounted(async () => {
  const userId = route.query.user_id
  const token = route.query.token

  if (typeof userId !== 'string' || typeof token !== 'string' || !userId || !token) {
    status.value = 'error'
    message.value = 'Ссылка недействительна: отсутствуют параметры.'
    return
  }

  try {
    await api(
      `/auth/verify?user_id=${encodeURIComponent(userId)}&token=${encodeURIComponent(token)}`,
      { method: 'POST', auth: false },
    )
    status.value = 'success'
    message.value = 'Email подтверждён. Теперь можно войти.'
  } catch (e) {
    status.value = 'error'
    if (e?.status === 0) message.value = 'Нет связи с сервером. Попробуй позже.'
    else if (e?.status === 400 || e?.status === 401 || e?.status === 404) {
      message.value = 'Ссылка недействительна или устарела. Запроси новую.'
    } else message.value = 'Не удалось подтвердить email. Попробуй позже.'
  }
})

function goToLogin() {
  router.push({ name: 'login', query: { verified: '1' } })
}
</script>

<template>
  <AuthShell>
    <div class="auth-card">
      <template v-if="status === 'loading'">
        <h1>Подтверждаем…</h1>
        <p class="auth-subtitle">Пожалуйста, подожди.</p>
      </template>

      <template v-else-if="status === 'success'">
        <h1>Готово</h1>
        <p class="auth-subtitle">{{ message }}</p>
        <button class="btn btn-primary btn-block" type="button" @click="goToLogin">Войти</button>
      </template>

      <template v-else>
        <h1>Не получилось</h1>
        <p class="form-error" role="alert">{{ message }}</p>
        <p class="auth-links">
          <RouterLink to="/login">Перейти ко входу</RouterLink>
        </p>
      </template>
    </div>
  </AuthShell>
</template>