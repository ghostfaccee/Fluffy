<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/AppShell.vue'
import ChatListItem from '@/components/ChatListItem.vue'
import MessageBubble from '@/components/MessageBubble.vue'

const route = useRoute()
const chat = useChatStore()
const auth = useAuthStore()

const text = ref('')
const sending = ref(false)
const error = ref('')
const messagesEl = ref(null)

const userId = computed(() => route.params.userId)
const current = computed(() => chat.chats[userId.value] || { messages: [], loading: false, hasMore: true })
const conversations = computed(() => chat.visibleConversations)

const currentConv = computed(() => conversations.value.find((c) => c.user_id === userId.value))

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

async function openChat(id) {
  if (!id) return
  if (id === auth.user?.user_id) {
    error.value = 'Нельзя открыть чат с самим собой.'
    return
  }
  error.value = ''
  try {
    await chat.loadChat(id)
    const msgs = current.value.messages
    const last = msgs[msgs.length - 1]
    if (last?.sender) {
      chat.upsertConversation(last.sender, {
        lastMessage: last.content,
        lastMessageAt: last.created_at,
      })
    } else if (msgs.length) {
      const firstFromOther = msgs.find((m) => m.sender_id !== auth.user?.user_id)
      if (firstFromOther?.sender) chat.upsertConversation(firstFromOther.sender)
    }
    chat.markRead(id)
    await scrollToBottom()
  } catch (e) {
    error.value = e?.status === 404 ? 'Пользователь не найден.' : 'Не удалось загрузить историю.'
  }
}

async function refresh() {
  if (document.hidden) return
  const id = userId.value
  if (!id) return
  try {
    await chat.loadChat(id)
  } catch {}
}

async function send() {
  const content = text.value.trim()
  if (!content || sending.value) return
  sending.value = true
  error.value = ''
  try {
    await chat.sendMessage(userId.value, content)
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

let intervalId = null
function onVisibility() {
  if (!document.hidden) refresh()
}

onMounted(() => {
  openChat(userId.value)
  intervalId = setInterval(refresh, 5000)
  document.addEventListener('visibilitychange', onVisibility)
})

onBeforeUnmount(() => {
  if (intervalId) clearInterval(intervalId)
  document.removeEventListener('visibilitychange', onVisibility)
})

watch(() => route.params.userId, (id) => openChat(id))
watch(() => current.value.messages.length, () => scrollToBottom())
</script>

<template>
  <AppShell>
    <div class="container">
      <div class="chats-layout">
        <aside class="chats-sidebar">
          <ChatListItem
            v-for="c in conversations"
            :key="c.user_id"
            :conversation="c"
            :active="c.user_id === userId"
          />
        </aside>

        <div class="chat-panel">
          <div ref="messagesEl" class="chat-messages">
            <p v-if="current.loading && !current.messages.length" class="app-hint">Загружаем…</p>
            <p v-else-if="!current.messages.length" class="app-hint">Пока нет сообщений. Напиши первым.</p>
            <MessageBubble
              v-for="m in current.messages"
              :key="m.message_id"
              :message="m"
            />
          </div>

          <form class="chat-input" @submit.prevent="send">
            <p v-if="error" class="form-error" role="alert">{{ error }}</p>
            <div class="chat-input-row">
              <textarea
                v-model="text"
                class="chat-textarea"
                rows="1"
                placeholder="Написать сообщение…"
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