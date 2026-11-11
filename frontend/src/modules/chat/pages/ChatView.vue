<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/modules/chat/stores/chat'
import { useAuthStore } from '@/stores/auth'
import { useWsStore } from '@/stores/ws'
import AppShell from '@/components/AppShell.vue'
import ChatListItem from '@/components/ChatListItem.vue'
import MessageBubble from '@/components/MessageBubble.vue'

const route = useRoute()
const chat = useChatStore()
const auth = useAuthStore()
const ws = useWsStore()

const text = ref('')
const sending = ref(false)
const error = ref('')
const messagesEl = ref(null)

const userId = computed(() => route.params.userId)

const current = computed(() =>
  chat.chats[userId.value] || {
    messages: [],
    loading: false,
    hasMore: true,
  },
)

const conversations = computed(() => chat.visibleConversations)

const currentConv = computed(() =>
  conversations.value.find((conversation) => conversation.user_id === userId.value),
)

async function scrollToBottom() {
  await nextTick()

  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function openChat(id) {
  if (!id) return

  if (String(id) === String(auth.user?.user_id)) {
    error.value = 'Нельзя открыть чат с самим собой.'
    return
  }

  error.value = ''

  try {
    await chat.loadChat(id)

    // Не обновляем интерфейс, если пользователь уже открыл другой чат.
    if (String(userId.value) !== String(id)) return

    const messages = chat.chats[id]?.messages || []
    const last = messages[messages.length - 1]

    const existing = chat.visibleConversations.find(
      (conversation) => String(conversation.user_id) === String(id),
    )

    // Данные собеседника могут находиться как в sender, так и в receiver.
    let otherUser = null

    for (const message of messages) {
      if (
        message.sender &&
        String(message.sender.user_id) === String(id)
      ) {
        otherUser = message.sender
        break
      }

      if (
        message.receiver &&
        String(message.receiver.user_id) === String(id)
      ) {
        otherUser = message.receiver
        break
      }
    }

    if (messages.length || existing) {
      const extra = last
        ? {
            lastMessage: last.content,
            lastMessageAt: last.created_at,
          }
        : {}

      chat.upsertConversation(
        {
          user_id: id,
          username: otherUser?.username || existing?.username || null,
          name: otherUser?.name || existing?.name || null,
          avatar_url: otherUser?.avatar_url || existing?.avatar_url || null,
        },
        extra,
      )
    }

    await chat.markRead(id)
    await scrollToBottom()
  } catch (cause) {
    if (String(userId.value) !== String(id)) return

    error.value =
      cause?.status === 404
        ? 'Пользователь не найден.'
        : 'Не удалось загрузить историю.'
  }
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

function onKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

let fallbackIntervalId = null
let unsubscribeReconnect = null

function syncCurrentChat() {
  const id = userId.value
  if (!id || document.hidden) return

  chat.loadChat(id).catch(() => {})
}

onMounted(() => {
  openChat(userId.value)

  // Основной канал — WebSocket. Опрос нужен только при потере соединения.
  fallbackIntervalId = setInterval(() => {
    if (!ws.connected) syncCurrentChat()
  }, 30000)

  // После переподключения загружаем пропущенные сообщения.
  unsubscribeReconnect = ws.on('connected', syncCurrentChat)
})

onBeforeUnmount(() => {
  if (fallbackIntervalId) clearInterval(fallbackIntervalId)
  if (unsubscribeReconnect) unsubscribeReconnect()
})

watch(
  () => route.params.userId,
  (id) => openChat(id),
)

watch(
  () => current.value.messages.length,
  () => scrollToBottom(),
)
</script>

<template>
  <AppShell>
    <div class="messenger">
      <aside class="messenger__sidebar">
        <header class="messenger__sidebar-head">
          <strong>Диалоги</strong>
          <span>{{ conversations.length }}</span>
        </header>

        <div class="messenger__dialogs">
          <p v-if="!conversations.length" class="messenger__hint">
            Здесь появятся ваши переписки.
          </p>

          <ChatListItem
            v-for="conversation in conversations"
            :key="conversation.user_id"
            :conversation="conversation"
            :active="conversation.user_id === userId"
          />
        </div>
      </aside>

      <section class="messenger__panel" aria-label="Переписка">
        <header class="messenger__head">
          <RouterLink
            :to="{ name: 'chats' }"
            class="messenger__back"
            aria-label="Вернуться к диалогам"
          >
            ←
          </RouterLink>

          <div class="messenger__person">
            <strong>
              {{ currentConv?.name || currentConv?.username || 'Переписка' }}
            </strong>

            <span v-if="currentConv?.username">
              @{{ currentConv.username }}
            </span>
          </div>

          <span class="messenger__connection">
            {{ ws.connected ? 'На связи' : 'Подключение…' }}
          </span>
        </header>

        <div
          ref="messagesEl"
          class="messenger__messages"
          aria-label="История сообщений"
          :aria-busy="current.loading"
        >
          <p
            v-if="current.loading && !current.messages.length"
            class="messenger__hint"
            role="status"
          >
            Загружаем переписку…
          </p>

          <div
            v-else-if="!current.messages.length"
            class="messenger__empty"
          >
            <strong>Начните разговор</strong>
            <p>Первое сообщение — начало чего-то хорошего.</p>
          </div>

          <MessageBubble
            v-for="message in current.messages"
            :key="message.message_id"
            :message="message"
          />
        </div>

        <form class="messenger__composer" @submit.prevent="send">
          <p v-if="error" class="messenger__error" role="alert">
            {{ error }}
          </p>

          <div class="messenger__input-row">
            <textarea
              v-model="text"
              class="messenger__textarea"
              rows="2"
              placeholder="Написать сообщение…"
              aria-label="Текст сообщения"
              maxlength="4000"
              :disabled="sending"
              @keydown="onKeydown"
            />

            <button
              class="messenger__send"
              type="submit"
              :disabled="sending || !text.trim()"
              :aria-label="sending ? 'Отправляем сообщение' : 'Отправить сообщение'"
            >
              {{ sending ? '…' : '↑' }}
            </button>
          </div>

          <span class="messenger__keyboard">
            Enter — отправить · Shift + Enter — новая строка
          </span>
        </form>
      </section>
    </div>
  </AppShell>
</template>

<style scoped src="../styles/chat.css"></style>
