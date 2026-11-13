<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useGroupStore } from '@/modules/groups/stores/group'
import { useAuthStore } from '@/stores/auth'
import { useWsStore } from '@/stores/ws'
import AppShell from '@/app/layouts/AppShell.vue'
import GroupAvatar from '@/modules/groups/components/GroupAvatar.vue'
import GroupListItem from '@/modules/groups/components/GroupListItem.vue'

const route = useRoute()
const groupStore = useGroupStore()
const ws = useWsStore()
const auth = useAuthStore()

const text = ref('')
const sending = ref(false)
const error = ref('')
const messagesEl = ref(null)

const groupId = computed(() => route.params.groupId)

const group = computed(() =>
  groupStore.groups.find((item) => item.group_id === groupId.value) || null,
)

const current = computed(() =>
  groupStore.chats[groupId.value] || {
    messages: [],
    loading: false,
    hasMore: true,
  },
)

async function scrollToBottom() {
  await nextTick()

  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function openGroup(id) {
  if (!id) return

  error.value = ''

  try {
    if (!group.value) {
      await groupStore.fetchGroup(id)
    }

    await groupStore.loadChat(id)
    await scrollToBottom()
  } catch (cause) {
    if (cause?.status === 404) {
      error.value = 'Группа не найдена.'
    } else if (cause?.status === 403) {
      error.value = 'Ты не участник этой группы.'
    } else {
      error.value = 'Не удалось загрузить группу.'
    }
  }
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

function onKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

function timeOf(iso) {
  if (!iso) return ''

  return new Date(iso).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}

let fallbackIntervalId = null
let unsubscribeReconnect = null

function syncCurrentGroup() {
  const id = groupId.value
  if (!id || document.hidden) return

  groupStore.loadChat(id).catch(() => {})
}

onMounted(() => {
  openGroup(groupId.value)

  // WebSocket — основной канал, опрос — резерв при потере соединения.
  fallbackIntervalId = setInterval(() => {
    if (!ws.connected) {
      syncCurrentGroup()
    }
  }, 30000)

  // Загружаем сообщения, пропущенные во время отключения.
  unsubscribeReconnect = ws.on('connected', syncCurrentGroup)
})

onBeforeUnmount(() => {
  if (fallbackIntervalId) {
    clearInterval(fallbackIntervalId)
  }

  if (unsubscribeReconnect) {
    unsubscribeReconnect()
  }
})

watch(
  () => route.params.groupId,
  (id) => openGroup(id),
)

watch(
  () => current.value.messages.length,
  () => scrollToBottom(),
)
</script>

<template>
  <AppShell>
    <div class="container">
      <div class="groups-actions group-page-actions">
        <RouterLink
          :to="{ name: 'group-members', params: { groupId } }"
          class="btn btn-secondary"
        >
          Участники
        </RouterLink>

        <RouterLink
          :to="{ name: 'group-settings', params: { groupId } }"
          class="btn btn-secondary"
        >
          Настройки группы
        </RouterLink>
      </div>

      <div class="chats-layout">
        <aside class="chats-sidebar">
          <GroupListItem
            v-for="item in groupStore.groups"
            :key="item.group_id"
            :group="item"
            :active="item.group_id === groupId"
          />
        </aside>

        <div class="chat-panel">
          <div ref="messagesEl" class="chat-messages">
            <p
              v-if="current.loading && !current.messages.length"
              class="app-hint"
            >
              Загружаем…
            </p>

            <p
              v-else-if="!current.messages.length"
              class="app-hint"
            >
              Пока нет сообщений. Напиши первым.
            </p>

            <div
              v-for="message in current.messages"
              :key="message.message_id"
              class="msg-row"
              :class="{
                'msg-row--mine': message.sender_id === auth.user?.user_id,
              }"
            >
              <GroupAvatar
                v-if="
                  message.sender_id !== auth.user?.user_id &&
                  message.sender
                "
                :group="{
                  name: message.sender.username,
                  avatar_url: message.sender.avatar_url,
                }"
                :size="32"
              />

              <div
                class="msg-bubble"
                :class="{
                  'msg-bubble--mine': message.sender_id === auth.user?.user_id,
                }"
              >
                <div
                  v-if="message.sender_id !== auth.user?.user_id"
                  class="msg-sender"
                >
                  {{ message.sender?.name || message.sender?.username || '…' }}
                </div>

                <div class="msg-content">
                  {{ message.content }}
                </div>

                <div class="msg-meta">
                  <span class="msg-time">
                    {{ timeOf(message.created_at) }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <form class="chat-input" @submit.prevent="send">
            <p v-if="error" class="form-error" role="alert">
              {{ error }}
            </p>

            <div class="chat-input-row">
              <textarea
                v-model="text"
                class="chat-textarea"
                rows="1"
                placeholder="Написать в группу…"
                maxlength="4000"
                @keydown="onKeydown"
              ></textarea>

              <button
                class="btn btn-primary"
                type="submit"
                :disabled="sending || !text.trim()"
              >
                {{ sending ? '…' : 'Отправить' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped src="../styles/group-page.css"></style>
