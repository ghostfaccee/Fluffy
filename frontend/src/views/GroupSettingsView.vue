<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGroupStore } from '@/stores/group'
import { useGroupAvatarUpload } from '@/composables/useGroupAvatarUpload'
import AppShell from '@/components/AppShell.vue'
import GroupAvatar from '@/components/GroupAvatar.vue'

const route = useRoute()
const router = useRouter()
const groupStore = useGroupStore()

const groupId = computed(() => route.params.groupId)
const group = computed(() => groupStore.groups.find((g) => g.group_id === groupId.value) || null)

const { uploading, error: avatarError, upload, remove } = useGroupAvatarUpload(groupId)
const fileInput = ref(null)

function pickFile() { fileInput.value?.click() }
async function onFileChange(e) {
  const file = e.target.files?.[0]
  e.target.value = ''
  if (!file) return
  try { await upload(file) } catch {}
}
async function onRemoveAvatar() { await remove() }

const form = ref({ name: '', description: '' })
const saveLoading = ref(false)
const saveError = ref('')
const saveSuccess = ref(false)

function fillForm() {
  if (!group.value) return
  form.value = {
    name: group.value.name || '',
    description: group.value.description || '',
  }
}

async function save() {
  if (saveLoading.value) return
  saveError.value = ''
  saveSuccess.value = false
  saveLoading.value = true
  try {
    const payload = {}
    if (form.value.name !== group.value.name) payload.name = form.value.name.trim()
    if ((form.value.description || '') !== (group.value.description || '')) {
      payload.description = form.value.description.trim() || null
    }
    if (!Object.keys(payload).length) return
    await groupStore.updateGroup(groupId.value, payload)
    saveSuccess.value = true
  } catch (e) {
    saveError.value = e?.status === 403 ? 'Недостаточно прав.' : 'Не удалось сохранить.'
  } finally {
    saveLoading.value = false
  }
}

const inviteToken = computed(() => group.value?.invite_token || '')
const inviteRegenLoading = ref(false)
async function regenInvite() {
  if (inviteRegenLoading.value) return
  inviteRegenLoading.value = true
  try { await groupStore.regenerateInviteToken(groupId.value) } catch {}
  finally { inviteRegenLoading.value = false }
}
function copyInvite() {
  if (inviteToken.value) navigator.clipboard?.writeText(inviteToken.value)
}

const leaveLoading = ref(false)
const deleteLoading = ref(false)
const dangerError = ref('')

async function leave() {
  if (!confirm('Выйти из группы?')) return
  leaveLoading.value = true
  dangerError.value = ''
  try {
    await groupStore.leaveGroup(groupId.value)
    router.push({ name: 'groups' })
  } catch (e) {
    dangerError.value = e?.status === 403 ? 'Владелец не может выйти, удали группу.' : 'Не удалось выйти.'
    leaveLoading.value = false
  }
}

async function destroy() {
  if (!confirm('Удалить группу? Это необратимо.')) return
  deleteLoading.value = true
  dangerError.value = ''
  try {
    await groupStore.deleteGroup(groupId.value)
    router.push({ name: 'groups' })
  } catch (e) {
    dangerError.value = e?.status === 403 ? 'Только владелец может удалить.' : 'Не удалось удалить.'
    deleteLoading.value = false
  }
}

onMounted(async () => {
  if (!group.value) await groupStore.fetchGroup(groupId.value)
  fillForm()
})
</script>

<template>
  <AppShell>
    <div class="container">
      <div class="groups-actions" style="margin-bottom: 18px;">
        <RouterLink :to="{ name: 'group', params: { groupId } }" class="btn btn-secondary">← К чату</RouterLink>
      </div>

      <div class="settings-card">
        <h2 class="settings-card-title">Аватар группы</h2>
        <p v-if="avatarError" class="form-error" role="alert">{{ avatarError }}</p>
        <div class="app-profile-row" style="margin-top: 8px;">
          <div class="app-profile-avatar">
            <GroupAvatar v-if="group" :group="group" :size="128" />
            <div class="app-profile-avatar-actions">
              <button class="btn btn-secondary btn-small" type="button" :disabled="uploading" @click="pickFile">
                {{ uploading ? 'Загружаем…' : 'Загрузить' }}
              </button>
              <button v-if="group?.avatar_url" class="btn btn-secondary btn-small" type="button" :disabled="uploading" @click="onRemoveAvatar">
                Удалить
              </button>
              <input ref="fileInput" type="file" accept="image/jpeg,image/png" hidden @change="onFileChange" />
            </div>
          </div>
        </div>
      </div>

      <form class="settings-card" @submit.prevent="save">
        <h2 class="settings-card-title">Основное</h2>
        <p v-if="saveError" class="form-error" role="alert">{{ saveError }}</p>
        <p v-if="saveSuccess" class="form-info" role="status">Сохранено.</p>
        <div class="field">
          <label for="gs-name">Название</label>
          <input id="gs-name" v-model="form.name" type="text" minlength="1" maxlength="40" required />
        </div>
        <div class="field">
          <label for="gs-desc">Описание</label>
          <input id="gs-desc" v-model="form.description" type="text" maxlength="200" />
        </div>
        <div class="settings-actions">
          <button class="btn btn-primary" type="submit" :disabled="saveLoading">
            {{ saveLoading ? 'Сохраняем…' : 'Сохранить' }}
          </button>
        </div>
      </form>

      <div class="settings-card">
        <h2 class="settings-card-title">Инвайт-токен</h2>
        <p class="settings-card-hint">Передай этот токен, чтобы пригласить в группу.</p>
        <div class="invite-row">
          <code class="invite-token">{{ inviteToken || '—' }}</code>
          <button class="btn btn-secondary btn-small" type="button" @click="copyInvite">Копировать</button>
          <button class="btn btn-secondary btn-small" type="button" :disabled="inviteRegenLoading" @click="regenInvite">
            {{ inviteRegenLoading ? '…' : 'Обновить' }}
          </button>
        </div>
      </div>

      <div class="settings-card settings-card--danger">
        <span class="settings-card-label">Danger</span>
        <h2 class="settings-card-title">Опасная зона</h2>
        <p v-if="dangerError" class="form-error" role="alert">{{ dangerError }}</p>
        <div class="settings-actions">
          <button class="btn btn-danger" type="button" :disabled="leaveLoading" @click="leave">
            {{ leaveLoading ? 'Выходим…' : 'Выйти из группы' }}
          </button>
          <button class="btn btn-danger" type="button" :disabled="deleteLoading" @click="destroy">
            {{ deleteLoading ? 'Удаляем…' : 'Удалить группу' }}
          </button>
        </div>
      </div>
    </div>
  </AppShell>
</template>