<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { registerErrorMessage } from '@/api/errors'
import AuthShell from '@/components/AuthShell.vue'

const auth = useAuthStore()

const username = ref('')
const name = ref('')
const email = ref('')
const password = ref('')
const bio = ref('')
const city = ref('')
const university = ref('')
const institute = ref('')
const group = ref('')

const loading = ref(false)
const error = ref('')
const done = ref(false)

const usernameValid = computed(() => {
  const v = username.value.trim()
  return v.length >= 3 && v.length <= 20
})
const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value.trim()))
const passwordValid = computed(() => {
  const v = password.value
  return v.length >= 4 && v.length <= 10
})
const formValid = computed(
  () => usernameValid.value && name.value.trim().length > 0 && emailValid.value && passwordValid.value,
)

async function submitRegistration() {
  if (loading.value) return
  error.value = ''
  loading.value = true
  try {
    const payload = {
      username: username.value.trim(),
      name: name.value.trim(),
      email: email.value.trim(),
      password: password.value,
    }
    for (const [key, refVal] of Object.entries({ bio, city, university, institute, group })) {
      const val = refVal.value.trim()
      if (val) payload[key] = val
    }

    await auth.register(payload)
    done.value = true
  } catch (e) {
    error.value = registerErrorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthShell>
    <div class="auth-card">
      <form v-if="!done" @submit.prevent="submitRegistration">
        <h1>Регистрация</h1>
        <p class="auth-subtitle">Создай аккаунт, чтобы присоединиться к Fluffy.</p>

        <p v-if="error" class="form-error" role="alert">{{ error }}</p>

        <div class="field">
          <label for="username">Логин</label>
          <input id="username" v-model="username" type="text" autocomplete="username" placeholder="username" minlength="3" maxlength="20" required />
        </div>
        <div class="field">
          <label for="name">Имя</label>
          <input id="name" v-model="name" type="text" autocomplete="name" placeholder="Как тебя зовут" required />
        </div>
        <div class="field">
          <label for="email">Email</label>
          <input id="email" v-model="email" type="email" autocomplete="email" placeholder="you@example.com" required />
        </div>
        <div class="field">
          <label for="password">Пароль</label>
          <input id="password" v-model="password" type="password" autocomplete="new-password" placeholder="От 4 до 10 символов" minlength="4" maxlength="10" required />
        </div>

        <p class="auth-hint">Остальное можно добавить позже в профиле.</p>

        <div class="field">
          <label for="bio">О себе <span class="label-optional">(опционально)</span></label>
          <input id="bio" v-model="bio" type="text" placeholder="Пара слов о себе" />
        </div>
        <div class="field">
          <label for="city">Город <span class="label-optional">(опционально)</span></label>
          <input id="city" v-model="city" type="text" placeholder="Где ты живёшь" />
        </div>
        <div class="field">
          <label for="university">Университет <span class="label-optional">(опционально)</span></label>
          <input id="university" v-model="university" type="text" placeholder="Какой у тебя ВУЗ"/>
        </div>
        <div class="field">
          <label for="institute">Институт <span class="label-optional">(опционально)</span></label>
          <input id="institute" v-model="institute" type="text" placeholder="Где ты учишься"/>
        </div>
        <div class="field">
          <label for="group">Группа <span class="label-optional">(опционально)</span></label>
          <input id="group" v-model="group" type="text" maxlength="20" placeholder="Твоя учебная группа"/>
        </div>

        <button class="btn btn-primary btn-block" type="submit" :disabled="loading || !formValid">
          {{ loading ? 'Создаём…' : 'Создать аккаунт' }}
        </button>

        <p class="auth-links">
          <span>Уже есть аккаунт?</span>
          <RouterLink to="/login">Войти</RouterLink>
        </p>
      </form>

      <div v-else>
        <h1>Проверь почту</h1>
        <p class="auth-subtitle">
          Мы отправили письмо на <strong>{{ email.trim() }}</strong>.
          Перейди по ссылке внутри, чтобы активировать аккаунт,
          а затем вернись и войди.
        </p>
        <p class="auth-links">
          <RouterLink to="/login">Перейти ко входу</RouterLink>
        </p>
      </div>
    </div>
  </AuthShell>
</template>