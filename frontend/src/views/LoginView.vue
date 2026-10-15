<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { loginErrorMessage, codeErrorMessage } from '@/api/errors'
import AuthShell from '@/components/AuthShell.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const step = ref('credentials')
const username = ref('')
const password = ref('')
const code = ref('')
const loading = ref(false)
const error = ref('')
const info = ref('')

const codeIsValid = computed(() => /^\d{4}$/.test(code.value))

onMounted(() => {
  if (route.query.verified === '1') {
    info.value = 'Email подтверждён. Войди, чтобы продолжить.'
  } else if (route.query.registered === '1') {
    info.value = 'Аккаунт создан. Подтверди почту и войди.'
  }
})

async function submitCredentials() {
  if (loading.value) return
  error.value = ''
  info.value = ''
  loading.value = true
  try {
    await auth.requestLoginCode(username.value.trim(), password.value)
    step.value = 'code'
  } catch (e) {
    error.value = loginErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function submitCode() {
  if (loading.value) return
  error.value = ''
  info.value = ''
  loading.value = true
  try {
    await auth.confirmLoginCode(username.value.trim(), code.value)
    const redirect = route.query.redirect
    const safe = typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//')
    router.push(safe ? redirect : '/app')
  } catch (e) {
    error.value = codeErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function resendCode() {
  if (loading.value) return
  error.value = ''
  info.value = ''
  loading.value = true
  try {
    await auth.requestLoginCode(username.value.trim(), password.value)
    code.value = ''
    info.value = 'Новый код отправлен на почту.'
  } catch (e) {
    error.value = loginErrorMessage(e)
  } finally {
    loading.value = false
  }
}

function backToCredentials() {
  step.value = 'credentials'
  code.value = ''
  error.value = ''
  info.value = ''
}
</script>

<template>
  <AuthShell>
    <div class="auth-card">
      <form v-if="step === 'credentials'" @submit.prevent="submitCredentials">
        <h1>Вход</h1>
        <p class="auth-subtitle">Рады видеть тебя снова.</p>

        <p v-if="error" class="form-error" role="alert">{{ error }}</p>
        <p v-if="info" class="form-info" role="status">{{ info }}</p>

        <div class="field">
          <label for="username">Логин</label>
          <input id="username" v-model="username" type="text" autocomplete="username" placeholder="username" required />
        </div>
        <div class="field">
          <label for="password">Пароль</label>
          <input id="password" v-model="password" type="password" autocomplete="current-password" placeholder="••••••••" required />
        </div>

        <button class="btn btn-primary btn-block" type="submit" :disabled="loading || !username.trim() || !password">
          {{ loading ? 'Проверяем…' : 'Продолжить' }}
        </button>

        <p class="auth-links">
          <span>Нет аккаунта?</span>
          <RouterLink to="/register">Зарегистрироваться</RouterLink>
        </p>
      </form>

      <form v-else @submit.prevent="submitCode">
        <h1>Введи код</h1>
        <p class="auth-subtitle">
          Мы отправили 4-значный код на почту, привязанную к аккаунту
          <strong>{{ username.trim() }}</strong>. Он действует 5 минут.
        </p>

        <p v-if="error" class="form-error" role="alert">{{ error }}</p>
        <p v-if="info" class="form-info" role="status">{{ info }}</p>

        <div class="field">
          <label for="code">Код из письма</label>
          <input id="code" v-model="code" class="code-input" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="4" placeholder="0000" autofocus required />
        </div>

        <button class="btn btn-primary btn-block" type="submit" :disabled="loading || !codeIsValid">
          {{ loading ? 'Проверяем…' : 'Войти' }}
        </button>

        <p class="auth-links">
          <button class="link-button" type="button" :disabled="loading" @click="backToCredentials">← Назад</button>
          <button class="link-button" type="button" :disabled="loading" @click="resendCode">Отправить код ещё раз</button>
        </p>
      </form>
    </div>
  </AuthShell>
</template>