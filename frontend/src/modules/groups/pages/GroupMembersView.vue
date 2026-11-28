<script setup>
import { ref, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useGroupStore } from '@/modules/groups/stores/group'
import { useAuthStore } from '@/modules/auth/stores/auth'
import AppShell from '@/app/layouts/AppShell.vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import { fetchUserById } from '@/shared/api/users'

const route = useRoute()
const groupStore = useGroupStore()
const auth = useAuthStore()

const groupId = computed(() => route.params.groupId)
const members = computed(() => groupStore.members[groupId.value] || [])

const loading = ref(false)
const error = ref('')
const profiles = ref({})

const memberRows = computed(() => members.value.map((member) => ({
  ...member,
  profile: member.user_id === auth.user?.user_id ? auth.user : profiles.value[member.user_id],
})))
const unavailableProfiles = computed(() => memberRows.value.filter(({ profile }) => profile === null))

const myRole = computed(() => {
  const me = members.value.find(
    (member) => member.user_id === auth.user?.user_id,
  )

  return me?.role || null
})

const isOwner = computed(() => myRole.value === 'owner')

async function loadProfile(userId) {
  // Each group/account visit owns its own map, including in-flight lookups.
  const currentProfiles = profiles.value
  delete currentProfiles[userId]

  try {
    currentProfiles[userId] = await fetchUserById(userId)
  } catch {
    currentProfiles[userId] = null
  }
}

async function load(id, currentUserId, onCleanup) {
  let active = true
  onCleanup(() => { active = false })

  profiles.value = {}
  error.value = ''
  loading.value = Boolean(currentUserId)
  if (!currentUserId) return

  try {
    const list = await groupStore.fetchMembers(id)
    if (!active) return

    for (const { user_id: userId } of list) {
      if (userId !== currentUserId) void loadProfile(userId)
    }
  } catch (cause) {
    if (!active) return

    if (cause?.status === 404) {
      error.value = 'Группа не найдена.'
    } else if (cause?.status === 403) {
      error.value = 'Ты не участник группы.'
    } else {
      error.value = 'Не удалось загрузить участников.'
    }
  } finally {
    if (active) loading.value = false
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

watch(
  [groupId, () => auth.user?.user_id],
  ([id, userId], _, onCleanup) => load(id, userId, onCleanup),
  { immediate: true },
)
</script>

<template>
  <AppShell>
    <div class="container">
      <div class="groups-actions group-page-actions">
        <RouterLink
          :to="{ name: 'group', params: { groupId } }"
          class="btn btn-secondary"
        >
          ← К чату
        </RouterLink>
      </div>

      <section class="app-section">
        <p v-if="loading" class="app-hint">
          Загружаем…
        </p>

        <p v-else-if="error" class="form-error" role="alert">
          {{ error }}
        </p>

        <p v-else-if="!members.length" class="app-hint">
          Участников нет.
        </p>

        <div v-else class="members-list">
          <div
            v-for="member in memberRows"
            :key="member.user_id"
            class="member-row"
          >
            <div class="member-body">
              <RouterLink
                v-if="member.profile?.username"
                :to="member.user_id === auth.user?.user_id
                  ? { name: 'me' }
                  : { name: 'user', params: { username: member.profile.username } }"
                class="member-identity"
              >
                <UserAvatar :user="member.profile" :size="40" />
                <span class="member-identity__text">
                  <span v-if="member.profile.name" class="member-name">{{ member.profile.name }}</span>
                  <span :class="member.profile.name ? 'member-username' : 'member-name'">
                    @{{ member.profile.username }}
                  </span>
                  <span class="member-role">{{ member.role }}</span>
                </span>
              </RouterLink>
              <div v-else class="member-identity">
                <UserAvatar :user="{}" :size="40" />
                <span class="member-identity__text">
                  <span class="member-name">{{ member.profile === null ? 'Профиль недоступен' : 'Загружаем профиль…' }}</span>
                  <span class="member-role">{{ member.role }}</span>
                </span>
              </div>
            </div>

            <div class="app-profile-actions">
              <button
                v-if="
                  isOwner &&
                  member.role !== 'owner' &&
                  member.user_id !== auth.user?.user_id
                "
                class="btn btn-secondary btn-small"
                type="button"
                @click="changeRole(member.user_id, member.role)"
              >
                {{
                  member.role === 'admin'
                    ? 'Понизить до участника'
                    : 'Повысить до админа'
                }}
              </button>

              <button
                v-if="
                  member.role !== 'owner' &&
                  member.user_id !== auth.user?.user_id
                "
                class="btn btn-secondary btn-small"
                type="button"
                @click="kick(member.user_id)"
              >
                Кикнуть
              </button>
            </div>
          </div>
        </div>
        <button
          v-if="!loading && !error && unavailableProfiles.length"
          class="btn btn-secondary btn-small member-retry"
          type="button"
          @click="unavailableProfiles.forEach(({ user_id }) => loadProfile(user_id))"
        >
          Повторить загрузку профилей
        </button>
      </section>
    </div>
  </AppShell>
</template>

<style scoped src="../styles/group-page.css"></style>

<style scoped>
.member-row {
  flex-wrap: wrap;
}

.member-body {
  flex-basis: 160px;
}

.member-identity {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text);
}

a.member-identity:hover .member-name {
  text-decoration: underline;
}

.member-identity__text {
  display: grid;
  min-width: 0;
}

.member-username {
  overflow: hidden;
  color: var(--muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-retry {
  margin-top: 12px;
}
</style>
