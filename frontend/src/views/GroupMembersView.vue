<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGroupStore } from '@/stores/group'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/AppShell.vue'
import UserAvatar from '@/components/UserAvatar.vue'

const route = useRoute()
const router = useRouter()
const groupStore = useGroupStore()
const auth = useAuthStore()

const groupId = computed(() => route.params.groupId)
const members = computed(() => groupStore.members[groupId.value] || [])
const loading = ref(false)
const error = ref('')

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

onMounted(load)
</script>

<template>
  <AppShell>
    <div class="container">

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
            <UserAvatar :user="{ user_id: m.user_id, username: m.user_id, name: null, avatar_url: null }" :size="40" />
            <div class="member-body">
              <div class="member-name">{{ m.user_id }}</div>
              <div class="member-role">{{ m.role }}</div>
            </div>
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
      </section>
    </div>
  </AppShell>
</template>