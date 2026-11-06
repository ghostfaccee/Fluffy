<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useGroupStore } from '@/stores/group'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/AppShell.vue'

const route = useRoute()
const groupStore = useGroupStore()
const auth = useAuthStore()

const groupId = computed(() => route.params.groupId)
const members = computed(() => groupStore.members[groupId.value] || [])
const loading = ref(false)
const error = ref('')

const myRole = computed(() => {
  const me = members.value.find((m) => m.user_id === auth.user?.user_id)
  return me?.role || null
})

const isOwner = computed(() => myRole.value === 'owner')

async function load() {
  loading.value = true
  error.value = ''
  try {
    await groupStore.fetchMembers(groupId.value)
  } catch (e) {
    if (e?.status === 404) error.value = 'Группа не найдена.'
    else if (e?.status === 403) error.value = 'Ты не участник группы.'
    else error.value = 'Не удалось загрузить участников.'
  } finally {
    loading.value = false
  }
}

async function kick(userId) {
  if (!confirm('Кикнуть этого участника?')) return
  try {
    await groupStore.kickMember(groupId.value, userId)
  } catch {
    error.value = 'Не удалось кикнуть участника.'
  }
}

async function changeRole(userId, currentRole) {
  const newRole = currentRole === 'admin' ? 'member' : 'admin'
  try {
    await groupStore.changeRole(groupId.value, userId, newRole)
  } catch {
    error.value = 'Не удалось изменить роль.'
  }
}

onMounted(load)
</script>

<template>
  <AppShell>
    <div class="container">
      <section class="app-section app-section--hero">
        <span class="eyebrow"><span class="status-dot"></span>Участники</span>
        <h1 class="app-title app-title--hero">
          <span class="gradient-text">Участники группы.</span>
        </h1>
      </section>

      <div class="groups-actions" style="margin-bottom: 18px;">
        <RouterLink :to="{ name: 'group', params: { groupId } }" class="btn btn-secondary">
          ← К чату
        </RouterLink>
      </div>

      <section class="app-section">
        <p v-if="loading" class="app-hint">Загружаем…</p>
        <p v-else-if="error" class="form-error" role="alert">{{ error }}</p>
        <p v-else-if="!members.length" class="app-hint">Участников нет.</p>
        <div v-else class="members-list">
          <div v-for="m in members" :key="m.user_id" class="member-row">
            <div class="member-body">
              <div class="member-name">{{ m.user_id }}</div>
              <div class="member-role">{{ m.role }}</div>
            </div>

            <div class="app-profile-actions">
              <button
                v-if="isOwner && m.role !== 'owner' && m.user_id !== auth.user?.user_id"
                class="btn btn-secondary btn-small"
                type="button"
                @click="changeRole(m.user_id, m.role)"
              >
                {{ m.role === 'admin' ? 'Понизить до участника' : 'Повысить до админа' }}
              </button>

              <button
                v-if="m.role !== 'owner' && m.user_id !== auth.user?.user_id"
                class="btn btn-secondary btn-small"
                type="button"
                @click="kick(m.user_id)"
              >
                Кикнуть
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </AppShell>
</template>