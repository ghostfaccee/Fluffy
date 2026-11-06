<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useAvatarUpload } from '@/composables/useAvatarUpload'
import { profileErrorMessage } from '@/api/errors'
import AppShell from '@/components/AppShell.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import UserCard from '@/components/UserCard.vue'

const auth = useAuthStore()
const { uploading, error: avatarError, upload, remove } = useAvatarUpload()

const user = computed(() => auth.user)

const fileInput = ref(null)
const editMode = ref(false)
const form = ref({
  name: '',
  username: '',
  email: '',
  bio: '',
  city: '',
  university: '',
  institute: '',
  group: '',
})
const saveLoading = ref(false)
const saveError = ref('')
const saveSuccess = ref(false)

function pickFile() {
  fileInput.value?.click()
}

async function onFileChange(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  try {
    await upload(file)
  } catch {}
}

async function onRemoveAvatar() {
  await remove()
}

function startEdit() {
  const u = user.value
  form.value = {
    name: u.name || '',
    username: u.username || '',
    email: u.email || '',
    bio: u.bio || '',
    city: u.city || '',
    university: u.university || '',
    institute: u.institute || '',
    group: u.group || '',
  }
  saveError.value = ''
  saveSuccess.value = false
  editMode.value = true
}

function cancelEdit() {
  editMode.value = false
  saveError.value = ''
}

async function saveProfile() {
  if (saveLoading.value) return
  saveError.value = ''
  saveSuccess.value = false
  saveLoading.value = true
  try {
    const payload = {}
    const u = user.value
    for (const key of ['name', 'username', 'email', 'bio', 'city', 'university', 'institute', 'group']) {
      const val = form.value[key].trim()
      const current = u[key] || ''
      if (val !== current) payload[key] = val || null
    }
    if (Object.keys(payload).length === 0) {
      editMode.value = false
      return
    }
    await auth.updateProfile(payload)
    saveSuccess.value = true
    editMode.value = false
  } catch (e) {
    saveError.value = profileErrorMessage(e)
  } finally {
    saveLoading.value = false
  }
}
</script>

<template>
  <AppShell>
    <div class="container">
      <section class="app-section">
        <div class="app-profile-row">
          <div class="app-profile-avatar">
            <UserAvatar :user="user" :size="128" />
            <div class="app-profile-avatar-actions">
              <button class="btn btn-secondary btn-small" type="button" :disabled="uploading" @click="pickFile">
                {{ uploading ? 'Загружаем…' : 'Загрузить' }}
              </button>
              <button v-if="user?.avatar_url" class="btn btn-secondary btn-small" type="button" :disabled="uploading" @click="onRemoveAvatar">
                Удалить
              </button>
              <input ref="fileInput" type="file" accept="image/jpeg,image/png" hidden @change="onFileChange" />
            </div>
            <p v-if="avatarError" class="form-error" role="alert">{{ avatarError }}</p>
          </div>

          <div class="app-profile-info">
            <template v-if="!editMode">
              <UserCard :user="user" show-email hide-avatar />

              <div class="app-profile-actions">
                <button class="btn btn-primary" type="button" @click="startEdit">Редактировать</button>
              </div>

              <p v-if="saveSuccess" class="form-info" role="status">Профиль обновлён.</p>
            </template>

            <form v-else class="me-form" @submit.prevent="saveProfile">
              <p v-if="saveError" class="form-error" role="alert">{{ saveError }}</p>

              <div class="field">
                <label for="m-name">Имя</label>
                <input id="m-name" v-model="form.name" type="text" />
              </div>
              <div class="field">
                <label for="m-username">Логин</label>
                <input id="m-username" v-model="form.username" type="text" minlength="3" maxlength="20" />
              </div>
              <div class="field">
                <label for="m-email">Email</label>
                <input id="m-email" v-model="form.email" type="email" />
              </div>
              <div class="field">
                <label for="m-bio">О себе</label>
                <input id="m-bio" v-model="form.bio" type="text" />
              </div>
              <div class="field">
                <label for="m-city">Город</label>
                <input id="m-city" v-model="form.city" type="text" />
              </div>
              <div class="field">
                <label for="m-university">Университет</label>
                <input id="m-university" v-model="form.university" type="text" />
              </div>
              <div class="field">
                <label for="m-institute">Институт</label>
                <input id="m-institute" v-model="form.institute" type="text" />
              </div>
              <div class="field">
                <label for="m-group">Группа</label>
                <input id="m-group" v-model="form.group" type="text" maxlength="20" />
              </div>

              <div class="app-profile-actions">
                <button class="btn btn-primary" type="submit" :disabled="saveLoading">
                  {{ saveLoading ? 'Сохраняем…' : 'Сохранить' }}
                </button>
                <button class="btn btn-secondary" type="button" :disabled="saveLoading" @click="cancelEdit">
                  Отмена
                </button>
              </div>
            </form>
          </div>
        </div>
      </section>
    </div>
  </AppShell>
</template>