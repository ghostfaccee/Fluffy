<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { passwordErrorMessage } from '@/api/errors'
import AppShell from '@/components/AppShell.vue'

const auth = useAuthStore()
const router = useRouter()

// --- смена пароля ---
const passwordForm = ref({ old_password: '', new_password: '' })
const passwordLoading = ref(false)
const passwordError = ref('')
const passwordSuccess = ref(false)

async function changePassword() {
  if (passwordLoading.value) return
  passwordError.value = ''
  passwordSuccess.value = false
  passwordLoading.value = true
  try {
    await auth.updatePassword({
      old_password: passwordForm.value.old_password,
      new_password: passwordForm.value.new_password,
    })
    passwordSuccess.value = true
    passwordForm.value = { old_password: '', new_password: '' }
  } catch (e) {
    passwordError.value = passwordErrorMessage(e)
  } finally {
    passwordLoading.value = false
  }
}

// --- удаление аккаунта ---
const showDeleteConfirm = ref(false)
const deleteLoading = ref(false)
const deleteError = ref('')

function toggleDelete() {
  showDeleteConfirm.value = !showDeleteConfirm.value
  deleteError.value = ''
}

async function deleteAccount() {
  if (deleteLoading.value) return
  deleteError.value = ''
  deleteLoading.value = true
  try {
    await auth.deleteAccount()
    router.push({ name: 'landing' })
  } catch {
    deleteError.value = 'Не удалось удалить аккаунт.'
    deleteLoading.value = false
  }
}
</script>

<template>
  <AppShell>
    <div class="container">
      <section class="app-section">
        <div class="app-section--hero settings-hero">
        <span class="eyebrow">
            <span class="status-dot"></span>
            Настройки
        </span>
        <h1 class="app-title app-title--hero">
            Твои <span class="gradient-text">настройки.</span>
        </h1>
        <p class="app-welcome">
            Смена пароля и управление аккаунтом — здесь.
        </p>
        </div>

        <!-- Профиль -->
        <div class="settings-card">
          <div class="settings-card-head">
            <h2 class="settings-card-title">Профиль</h2>
            <p class="settings-card-hint">
              Имя, логин, email и остальные данные — в профиле.
            </p>
          </div>
          <RouterLink to="/me" class="btn btn-secondary">Открыть профиль</RouterLink>
        </div>

        <!-- Warning: смена пароля -->
        <div class="settings-card settings-card--warning">
          <span class="settings-card-label">Warning</span>
          <div class="settings-card-head">
            <h2 class="settings-card-title">Смена пароля</h2>
            <p class="settings-card-hint">
              После смены пароля все активные сессии будут завершены.
            </p>
          </div>

          <p v-if="passwordError" class="form-error" role="alert">{{ passwordError }}</p>
          <p v-if="passwordSuccess" class="form-info" role="status">Пароль изменён.</p>

          <form class="settings-form" @submit.prevent="changePassword">
            <div class="field">
              <label for="p-old">Старый пароль</label>
              <input id="p-old" v-model="passwordForm.old_password" type="password" minlength="3" maxlength="10" required />
            </div>
            <div class="field">
              <label for="p-new">Новый пароль</label>
              <input id="p-new" v-model="passwordForm.new_password" type="password" minlength="3" maxlength="10" required />
            </div>
            <div class="settings-actions">
              <button class="btn btn-secondary" type="submit" :disabled="passwordLoading">
                {{ passwordLoading ? 'Меняем…' : 'Сменить пароль' }}
              </button>
            </div>
          </form>
        </div>

        <!-- Danger: удаление -->
        <div class="settings-card settings-card--danger">
          <span class="settings-card-label">Danger</span>
          <div class="settings-card-head">
            <h2 class="settings-card-title">Удаление аккаунта</h2>
            <p class="settings-card-hint">
              Действие необратимо. Профиль и все данные будут удалены без возможности восстановления.
            </p>
          </div>

          <p v-if="deleteError" class="form-error" role="alert">{{ deleteError }}</p>

          <div v-if="!showDeleteConfirm">
            <button class="btn btn-danger" type="button" @click="toggleDelete">
              Удалить аккаунт
            </button>
          </div>

          <div v-else>
            <p class="settings-confirm">Точно удалить? Это необратимо.</p>
            <div class="settings-actions">
              <button class="btn btn-danger" type="button" :disabled="deleteLoading" @click="deleteAccount">
                {{ deleteLoading ? 'Удаляем…' : 'Да, удалить' }}
              </button>
              <button class="btn btn-secondary" type="button" :disabled="deleteLoading" @click="toggleDelete">
                Отмена
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </AppShell>
</template>