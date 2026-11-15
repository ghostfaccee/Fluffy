<script setup>
import { ref, computed } from 'vue'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { useAvatarUpload } from '@/modules/profile/composables/useAvatarUpload'
import UserCard from '@/modules/profile/components/UserCard.vue'
import ProfileMusic from '@/modules/profile/components/ProfileMusic.vue'
import { profileErrorMessage } from '@/shared/api/errors'
import AppShell from '@/app/layouts/AppShell.vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import ProfilePosts from '@/modules/posts/components/ProfilePosts.vue'

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

async function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''

  if (!file) return

  try {
    await upload(file)
  } catch {
    // Ошибка отображается через avatarError.
  }
}

async function onRemoveAvatar() {
  await remove()
}

function startEdit() {
  const current = user.value

  if (!current) return

  form.value = {
    name: current.name || '',
    username: current.username || '',
    email: current.email || '',
    bio: current.bio || '',
    city: current.city || '',
    university: current.university || '',
    institute: current.institute || '',
    group: current.group || '',
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
  if (saveLoading.value || !user.value) return

  saveError.value = ''
  saveSuccess.value = false
  saveLoading.value = true

  try {
    const payload = {}
    const current = user.value

    for (const key of [
      'name',
      'username',
      'email',
      'bio',
      'city',
      'university',
      'institute',
      'group',
    ]) {
      const value = form.value[key].trim()
      const previous = current[key] || ''

      if (value !== previous) {
        payload[key] = value || null
      }
    }

    if (Object.keys(payload).length === 0) {
      editMode.value = false
      return
    }

    await auth.updateProfile(payload)

    saveSuccess.value = true
    editMode.value = false
  } catch (cause) {
    saveError.value = profileErrorMessage(cause)
  } finally {
    saveLoading.value = false
  }
}
</script>

<template>
  <AppShell>
    <div class="container">
      <div class="profile-overview">
        <section class="app-section profile-overview__main">
          <div class="app-profile-row">
            <div class="app-profile-avatar">
              <UserAvatar :user="user" :size="128" />

              <div class="app-profile-avatar-actions">
                <button
                  class="btn btn-secondary btn-small"
                  type="button"
                  :disabled="uploading"
                  @click="pickFile"
                >
                  {{ uploading ? 'Загружаем…' : 'Загрузить' }}
                </button>

                <button
                  v-if="user?.avatar_url"
                  class="btn btn-secondary btn-small"
                  type="button"
                  :disabled="uploading"
                  @click="onRemoveAvatar"
                >
                  Удалить
                </button>

                <input
                  ref="fileInput"
                  type="file"
                  accept="image/jpeg,image/png"
                  hidden
                  @change="onFileChange"
                />
              </div>

              <p v-if="avatarError" class="form-error" role="alert">
                {{ avatarError }}
              </p>
            </div>

            <div class="app-profile-info">
              <template v-if="!editMode">
                <UserCard :user="user" show-email hide-avatar />

                <div class="app-profile-actions">
                  <button
                    class="btn btn-primary"
                    type="button"
                    @click="startEdit"
                  >
                    Редактировать
                  </button>
                </div>

                <p v-if="saveSuccess" class="form-info" role="status">
                  Профиль обновлён.
                </p>
              </template>

              <form v-else class="me-form" @submit.prevent="saveProfile">
                <p v-if="saveError" class="form-error" role="alert">
                  {{ saveError }}
                </p>

                <div class="field">
                  <label for="m-name">Имя</label>
                  <input id="m-name" v-model="form.name" type="text" />
                </div>

                <div class="field">
                  <label for="m-username">Логин</label>
                  <input
                    id="m-username"
                    v-model="form.username"
                    type="text"
                    minlength="3"
                    maxlength="20"
                  />
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
                  <input
                    id="m-university"
                    v-model="form.university"
                    type="text"
                  />
                </div>

                <div class="field">
                  <label for="m-institute">Институт</label>
                  <input
                    id="m-institute"
                    v-model="form.institute"
                    type="text"
                  />
                </div>

                <div class="field">
                  <label for="m-group">Группа</label>
                  <input
                    id="m-group"
                    v-model="form.group"
                    type="text"
                    maxlength="20"
                  />
                </div>

                <div class="app-profile-actions">
                  <button
                    class="btn btn-primary"
                    type="submit"
                    :disabled="saveLoading"
                  >
                    {{ saveLoading ? 'Сохраняем…' : 'Сохранить' }}
                  </button>

                  <button
                    class="btn btn-secondary"
                    type="button"
                    :disabled="saveLoading"
                    @click="cancelEdit"
                  >
                    Отмена
                  </button>
                </div>
              </form>
            </div>
          </div>
        </section>

        <aside
          v-if="user"
          class="profile-overview__side"
          aria-label="Музыка"
        >
          <ProfileMusic
            :key="user.user_id"
            :music-url="user.music_url"
            editable
          />
        </aside>
      </div>

      <ProfilePosts
        v-if="user?.username"
        :key="user.username"
        :username="user.username"
      />
    </div>
  </AppShell>
</template>

<style scoped>
.profile-overview {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 290px;
  align-items: start;
  gap: 20px;
  margin-bottom: 24px;
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

@media (max-width: 1100px) {
  .profile-overview {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
