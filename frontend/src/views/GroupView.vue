<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useGroupStore } from '@/stores/group'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/AppShell.vue'
import GroupAvatar from '@/components/GroupAvatar.vue'
import GroupListItem from '@/components/GroupListItem.vue'

const route = useRoute()
const groupStore = useGroupStore()
const auth = useAuthStore()

const text = ref('')
const sending = ref(false)
const error = ref('')
const messagesEl = ref(null)

const groupId = computed(() => route.params.groupId)
const group = computed(() => groupStore.groups.find((g) => g.group_id === groupId.value) || null)
const current = computed(() => groupStore.chats[groupId.value] || { messages: [], loading: false, hasMore: true })

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

async function openGroup(id) {
  if (!id) return
  error.value = ''
  try {
    if (!group.value) await groupStore.fetchGroup(id)
    await groupStore.loadChat(id)
    await scrollToBottom()
  } catch (e) {
    if (e?.status === 404) error.value = 'Группа не найдена.'
    else if (e?.status === 403) error.value = 'Ты не участник этой группы.'
    else error.value = 'Не удалось загрузить группу.'
  }
}

async function refresh() {
  if (document.hidden) return
  try { await groupStore.loadChat(groupId.value) } catch {}
}

async function send() {
  const content = text.value.trim()
  if (!content || sending.value) return
  sending.value = true
  error.value = ''
  try {
    await groupStore.sendMessage(groupId.value, content)
    text.value = ''
    await scrollToBottom()
  } catch {
    error.value = 'Не удалось отправить сообщение.'
  } finally {
    sending.value = false
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

function timeOf(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

let intervalId = null
function onVisibility() { if (!document.hidden) refresh() }

onMounted(() => {
  openGroup(groupId.value)
  intervalId = setInterval(refresh, 5000)
  document.addEventListener('visibilitychange', onVisibility)
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
  document.removeEventListener('visibilitychange', onVisibility)
})

watch(() => route.params.groupId, (id) => openGroup(id))
watch(() => current.value.messages.length, () => scrollToBottom())
</script>

<template>
  <AppShell>
    <div class="container">
      <section class="app-section app-section--hero">
        <h1 class="app-title app-title--hero">
          <span class="gradient-text">{{ group?.name || 'Группа' }}</span>
        </h1>
        <p v-if="group?.description" class="app-welcome">{{ group.description }}</p>
      </section>

      <div class="groups-actions" style="margin-bottom: 18px;">
        <RouterLink :to="{ name: 'group-members', params: { groupId } }" class="btn btn-secondary">
          Участники
        </RouterLink>
        <RouterLink :to="{ name: 'group-settings', params: { groupId } }" class="btn btn-secondary">
          Настройки группы
        </RouterLink>
      </div>

      <div class="chats-layout">
        <aside class="chats-sidebar">
          <GroupListItem
            v-for="g in groupStore.groups"
            :key="g.group_id"
            :group="g"
            :active="g.group_id === groupId"
          />
        </aside>

        <div class="chat-panel">
          <div ref="messagesEl" class="chat-messages">
            <p v-if="current.loading && !current.messages.length" class="app-hint">Загружаем…</p>
            <p v-else-if="!current.messages.length" class="app-hint">Пока нет сообщений. Напиши первым.</p>

            <div
              v-for="m in current.messages"
              :key="m.message_id"
              class="msg-row"
              :class="{ 'msg-row--mine': m.sender_id === auth.user?.user_id }"
            >
              <GroupAvatar
                v-if="m.sender_id !== auth.user?.user_id && m.sender"
                :group="{ name: m.sender.username, avatar_url: m.sender.avatar_url }"
                :size="32"
              />
              <div class="msg-bubble" :class="{ 'msg-bubble--mine': m.sender_id === auth.user?.user_id }">
                <div v-if="m.sender_id !== auth.user?.user_id" class="msg-sender">
                  {{ m.sender?.name || m.sender?.username || '…' }}
                </div>
                <div class="msg-content">{{ m.content }}</div>
                <div class="msg-meta">
                  <span class="msg-time">{{ timeOf(m.created_at) }}</span>
                </div>
              </div>
            </div>
          </div>

          <form class="chat-input" @submit.prevent="send">
            <p v-if="error" class="form-error" role="alert">{{ error }}</p>
            <div class="chat-input-row">
              <textarea
                v-model="text"
                class="chat-textarea"
                rows="1"
                placeholder="Написать в группу…"
                maxlength="4000"
                @keydown="onKeydown"
              ></textarea>
              <button class="btn btn-primary" type="submit" :disabled="sending || !text.trim()">
                {{ sending ? '…' : 'Отправить' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </AppShell>
</template>