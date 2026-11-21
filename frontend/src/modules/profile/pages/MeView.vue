<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { useAvatarUpload } from '@/modules/profile/composables/useAvatarUpload'
import UserCard from '@/modules/profile/components/UserCard.vue'
import ProfileMusic from '@/modules/profile/components/ProfileMusic.vue'
import { profileErrorMessage } from '@/shared/api/errors'
import AppShell from '@/app/layouts/AppShell.vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import ProfilePosts from '@/modules/posts/components/ProfilePosts.vue'
import ProfileStories from '@/modules/stories/components/ProfileStories.vue'

const auth = useAuthStore()
const { uploading, error: avatarError, upload, remove } = useAvatarUpload()

const user = computed(() => auth.user)

const fileInput = ref(null)
const editMode = ref(false)
const avatarActionLoading = ref(false)
const avatarActionError = ref('')

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

const avatarBusy = computed(
  () => uploading.value || avatarActionLoading.value,
)

const formBusy = computed(
  () => saveLoading.value || avatarBusy.value,
)

const displayedAvatarError = computed(
  () => avatarActionError.value || avatarError.value,
)

function pickFile() {
  if (formBusy.value) return

  fileInput.value?.click()
}

async function onFileChange(event) {
  const file = event.target.files?.[0]

  event.target.value = ''

  if (!file || formBusy.value) return

  avatarActionError.value = ''
  avatarActionLoading.value = true

  try {
    await upload(file)
  } catch {
    avatarActionError.value =
      avatarError.value || 'Не удалось изменить фотографию. Попробуйте снова.'
  } finally {
    avatarActionLoading.value = false
  }
}

async function onRemoveAvatar() {
  if (formBusy.value || !user.value?.avatar_url) return

  avatarActionError.value = ''
  avatarActionLoading.value = true

  try {
    await remove()
  } catch {
    avatarActionError.value =
      avatarError.value || 'Не удалось удалить фотографию. Попробуйте снова.'
  } finally {
    avatarActionLoading.value = false
  }
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
  avatarActionError.value = ''
  editMode.value = true
}

function cancelEdit() {
  if (formBusy.value) return

  editMode.value = false
  saveError.value = ''
  avatarActionError.value = ''
}

async function saveProfile() {
  if (formBusy.value || !user.value) return

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
      <template v-if="user">
        <div class="profile-overview">
          <section class="app-section profile-overview__main">
            <div class="app-profile-row profile-overview__row">
              <div class="app-profile-avatar profile-overview__avatar-column">
                <ProfileStories
                  :key="user.user_id"
                  :user="user"
                  :size="128"
                />
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
                  <section
                    class="me-form__avatar-section"
                    aria-labelledby="profile-avatar-title"
                  >
                    <h2 id="profile-avatar-title" class="me-form__section-title">
                      Фотография профиля
                    </h2>

                    <div class="me-form__avatar-row">
                      <div class="me-form__avatar-preview">
                        <UserAvatar :user="user" :size="64" />
                      </div>

                      <div class="me-form__avatar-controls">
                        <div class="me-form__avatar-buttons">
                          <button
                            class="btn btn-secondary btn-small"
                            type="button"
                            :disabled="formBusy"
                            @click="pickFile"
                          >
                            {{ avatarBusy ? 'Обрабатываем…' : 'Сменить фото' }}
                          </button>

                          <button
                            v-if="user.avatar_url"
                            class="btn btn-secondary btn-small"
                            type="button"
                            :disabled="formBusy"
                            @click="onRemoveAvatar"
                          >
                            Удалить фото
                          </button>
                        </div>

                        <p class="me-form__hint">
                          JPEG или PNG. Изменение фотографии сохраняется сразу.
                        </p>
                      </div>
                    </div>

                    <input
                      ref="fileInput"
                      type="file"
                      accept="image/jpeg,image/png"
                      :disabled="formBusy"
                      hidden
                      @change="onFileChange"
                    />

                    <p
                      v-if="displayedAvatarError"
                      class="form-error"
                      role="alert"
                    >
                      {{ displayedAvatarError }}
                    </p>
                  </section>

                  <p v-if="saveError" class="form-error" role="alert">
                    {{ saveError }}
                  </p>

                  <div class="field">
                    <label for="m-name">Имя</label>
                    <input
                      id="m-name"
                      v-model="form.name"
                      type="text"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="field">
                    <label for="m-username">Логин</label>
                    <input
                      id="m-username"
                      v-model="form.username"
                      type="text"
                      minlength="3"
                      maxlength="20"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="field">
                    <label for="m-email">Email</label>
                    <input
                      id="m-email"
                      v-model="form.email"
                      type="email"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="field">
                    <label for="m-bio">О себе</label>
                    <input
                      id="m-bio"
                      v-model="form.bio"
                      type="text"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="field">
                    <label for="m-city">Город</label>
                    <input
                      id="m-city"
                      v-model="form.city"
                      type="text"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="field">
                    <label for="m-university">Университет</label>
                    <input
                      id="m-university"
                      v-model="form.university"
                      type="text"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="field">
                    <label for="m-institute">Институт</label>
                    <input
                      id="m-institute"
                      v-model="form.institute"
                      type="text"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="field">
                    <label for="m-group">Группа</label>
                    <input
                      id="m-group"
                      v-model="form.group"
                      type="text"
                      maxlength="20"
                      :disabled="formBusy"
                    />
                  </div>

                  <div class="app-profile-actions">
                    <button
                      class="btn btn-primary"
                      type="submit"
                      :disabled="formBusy"
                    >
                      {{ saveLoading ? 'Сохраняем…' : 'Сохранить' }}
                    </button>

                    <button
                      class="btn btn-secondary"
                      type="button"
                      :disabled="formBusy"
                      @click="cancelEdit"
                    >
                      Отмена
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </section>

          <aside class="profile-overview__side" aria-label="Музыка">
            <ProfileMusic
              :key="user.user_id"
              :music-url="user.music_url"
              editable
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
  grid-template-columns: minmax(0, 1fr) 290px;
  align-items: start;
  gap: 20px;
  margin-bottom: 24px;
}

.profile-overview__main {
  min-width: 0;
  margin: 0;
}

.profile-overview__row {
  align-items: flex-start;
}

.profile-overview__avatar-column {
  flex: 0 0 196px;
  width: 196px;
  min-width: 0;
}

.profile-overview__main .app-profile-info {
  min-width: 0;
  overflow-wrap: anywhere;
}

.profile-overview__side {
  min-width: 0;
}

.me-form {
  display: grid;
  gap: 14px;
}

.me-form__avatar-section {
  display: grid;
  gap: 14px;
  padding-bottom: 20px;
  margin-bottom: 4px;
  border-bottom: 1px solid var(--border);
}

.me-form__section-title {
  margin: 0;
  color: var(--text);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
}

.me-form__avatar-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
}

.me-form__avatar-preview {
  display: inline-flex;
  flex: 0 0 auto;
}

.me-form__avatar-controls {
  flex: 1 1 160px;
  min-width: 0;
}

.me-form__avatar-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.me-form__hint {
  margin: 8px 0 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
}

@media (max-width: 1100px) {
  .profile-overview {
    grid-template-columns: minmax(0, 1fr);
  }
}

@media (max-width: 600px) {
  .profile-overview__row {
    flex-direction: column;
    align-items: stretch;
  }

  .profile-overview__avatar-column {
    flex: 0 0 auto;
    align-self: center;
    width: min(100%, 240px);
  }
}
</style>
