<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGroupStore } from '@/stores/group'
import AppShell from '@/components/AppShell.vue'
import GroupListItem from '@/components/GroupListItem.vue'

const groupStore = useGroupStore()
const router = useRouter()

const loading = ref(false)
const error = ref('')

const showCreate = ref(false)
const createName = ref('')
const createDescription = ref('')
const createLoading = ref(false)
const createError = ref('')

const showJoin = ref(false)
const joinToken = ref('')
const joinLoading = ref(false)
const joinError = ref('')

const groups = computed(() => groupStore.groups)

async function loadGroups() {
  loading.value = true
  error.value = ''
  try {
    await groupStore.fetchGroups()
  } catch {
    error.value = 'Не удалось загрузить группы.'
  } finally {
    loading.value = false
  }
}

async function submitCreate() {
  if (createLoading.value) return
  createError.value = ''
  const name = createName.value.trim()
  if (!name) return
  createLoading.value = true
  try {
    const group = await groupStore.createGroup({
      name,
      description: createDescription.value.trim() || null,
    })
    showCreate.value = false
    createName.value = ''
    createDescription.value = ''
    router.push({ name: 'group', params: { groupId: group.group_id } })
  } catch (e) {
    createError.value = e?.status === 422 ? 'Проверь название и описание.' : 'Не удалось создать группу.'
  } finally {
    createLoading.value = false
  }
}

async function submitJoin() {
  if (joinLoading.value) return
  joinError.value = ''
  const token = joinToken.value.trim()
  if (!token) return
  joinLoading.value = true
  try {
    const group = await groupStore.joinByToken(token)
    showJoin.value = false
    joinToken.value = ''
    router.push({ name: 'group', params: { groupId: group.group_id } })
  } catch (e) {
    if (e?.status === 404) joinError.value = 'Такой группы нет.'
    else if (e?.status === 409) joinError.value = 'Ты уже участник.'
    else joinError.value = 'Не удалось войти.'
  } finally {
    joinLoading.value = false
  }
}

onMounted(loadGroups)
</script>

<template>
  <AppShell>
    <div class="container">
      <section class="app-section app-section--hero">
        <h1 class="app-title app-title--hero">
          <span class="gradient-text">Группы</span>
        </h1>
        <p class="app-welcome">Создавай группы, приглашай друзей и общайся вместе.</p>
      </section>

      <div class="groups-actions">
        <button class="btn btn-primary" type="button" @click="showCreate = !showCreate">
          Создать группу
        </button>
        <button class="btn btn-secondary" type="button" @click="showJoin = !showJoin">
          Войти по инвайту
        </button>
      </div>

      <form v-if="showCreate" class="settings-card" @submit.prevent="submitCreate">
        <h2 class="settings-card-title">Новая группа</h2>
        <p v-if="createError" class="form-error" role="alert">{{ createError }}</p>
        <div class="field">
          <label for="g-name">Название</label>
          <input id="g-name" v-model="createName" type="text" minlength="1" maxlength="40" required />
        </div>
        <div class="field">
          <label for="g-desc">Описание <span class="label-optional">(опционально)</span></label>
          <input id="g-desc" v-model="createDescription" type="text" maxlength="200" />
        </div>
        <div class="settings-actions">
          <button class="btn btn-primary" type="submit" :disabled="createLoading || !createName.trim()">
            {{ createLoading ? 'Создаём…' : 'Создать' }}
          </button>
          <button class="btn btn-secondary" type="button" @click="showCreate = false">Отмена</button>
        </div>
      </form>

      <form v-if="showJoin" class="settings-card" @submit.prevent="submitJoin">
        <h2 class="settings-card-title">Войти по инвайту</h2>
        <p v-if="joinError" class="form-error" role="alert">{{ joinError }}</p>
        <div class="field">
          <label for="g-token">Инвайт-токен</label>
          <input id="g-token" v-model="joinToken" type="text" required />
        </div>
        <div class="settings-actions">
          <button class="btn btn-primary" type="submit" :disabled="joinLoading || !joinToken.trim()">
            {{ joinLoading ? 'Входим…' : 'Войти' }}
          </button>
          <button class="btn btn-secondary" type="button" @click="showJoin = false">Отмена</button>
        </div>
      </form>

      <section class="app-section">
        <p v-if="loading" class="app-hint">Загружаем…</p>
        <p v-else-if="error" class="form-error" role="alert">{{ error }}</p>
        <p v-else-if="!groups.length" class="app-hint">
          Пока нет групп. Создай свою или войди по инвайту.
        </p>
        <div v-else class="groups-grid">
          <RouterLink
            v-for="g in groups"
            :key="g.group_id"
            :to="{ name: 'group', params: { groupId: g.group_id } }"
            class="group-tile"
          >
            <GroupListItem :group="g" />
          </RouterLink>
        </div>
      </section>
    </div>
  </AppShell>
</template>