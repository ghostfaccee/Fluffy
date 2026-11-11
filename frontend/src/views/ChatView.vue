<script setup>
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/stores/chat'
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
const current = computed(() => chat.chats[userId.value] || { messages: [], loading: false, hasMore: true })
const conversations = computed(() => chat.visibleConversations)

const currentConv = computed(() => conversations.value.find((c) => c.user_id === userId.value))

async function scrollToBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
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

    // За время загрузки пользователь мог открыть другой диалог.
    if (String(userId.value) !== String(id)) return

    const messages = chat.chats[id]?.messages || []
    const last = messages[messages.length - 1]

    const existing = chat.visibleConversations.find(
      (conversation) => String(conversation.user_id) === String(id),
    )

    // Ищем данные именно собеседника, независимо от того,
    // кто отправил последнее сообщение.
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
  } catch (e) {
    if (String(userId.value) !== String(id)) return

    error.value =
      e?.status === 404
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

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
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

  // WebSocket delivers new messages. Only poll as a slow fallback while it is offline.
  fallbackIntervalId = setInterval(() => {
    if (!ws.connected) syncCurrentChat()
  }, 30000)

  // A reconnect may have happened after messages were missed while offline.
  unsubscribeReconnect = ws.on('connected', syncCurrentChat)
})

onBeforeUnmount(() => {
  if (fallbackIntervalId) clearInterval(fallbackIntervalId)
  if (unsubscribeReconnect) unsubscribeReconnect()
})

watch(() => route.params.userId, (id) => openChat(id))
watch(() => current.value.messages.length, () => scrollToBottom())
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
<style scoped>
.messenger {
  display: grid;
  grid-template-columns: 250px minmax(0, 1fr);
  height: min(740px, calc(100dvh - 190px));
  min-height: 380px;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--bg-card);
}

.messenger__sidebar {
  display: flex;
  flex-direction: column;
  min-height: 0;
  border-right: 1px solid var(--border);
}

.messenger__sidebar-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 66px;
  padding: 0 18px;
  border-bottom: 1px solid var(--border);
}

.messenger__sidebar-head strong {
  font-size: 14px;
}

.messenger__sidebar-head span {
  color: var(--muted);
  font-size: 12px;
}

.messenger__dialogs {
  min-height: 0;
  overflow-y: auto;
  padding: 8px;
}

.messenger__dialogs :deep(a) {
  border-radius: 10px;
}

.messenger__panel {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.messenger__head {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  min-height: 66px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
}

.messenger__person {
  display: grid;
  gap: 3px;
  min-width: 0;
}

.messenger__person strong {
  overflow: hidden;
  color: var(--text);
  font-size: 14px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.messenger__person span,
.messenger__connection {
  color: var(--muted);
  font-size: 11px;
}

.messenger__connection {
  margin-left: auto;
  white-space: nowrap;
}

.messenger__back {
  display: none;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 9px;
  color: var(--text);
}

.messenger__messages {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  padding: 20px;
  background: color-mix(in srgb, var(--bg) 45%, transparent);
  scrollbar-width: thin;
}

.messenger__empty {
  display: grid;
  align-content: center;
  min-height: 100%;
  padding: 30px 0;
  text-align: center;
}

.messenger__empty strong {
  font-size: 17px;
  font-weight: 600;
}

.messenger__empty p,
.messenger__hint {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.messenger__hint {
  padding: 12px;
}

.messenger__composer {
  flex-shrink: 0;
  padding: 14px 18px 10px;
  border-top: 1px solid var(--border);
}

.messenger__input-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
}

.messenger__textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 48px;
  max-height: 140px;
  resize: vertical;
  padding: 12px 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
  color: var(--text);
  font: inherit;
  font-size: 14px;
  line-height: 1.5;
}

.messenger__textarea::placeholder {
  color: var(--muted);
}

.messenger__send {
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  margin-bottom: 2px;
  border: 0;
  border-radius: 12px;
  background: var(--accent);
  color: var(--on-accent);
  font-size: 25px;
  font-weight: 600;
  cursor: pointer;
}

.messenger__send:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.messenger__keyboard {
  display: block;
  margin-top: 7px;
  color: var(--muted);
  font-size: 10px;
}

.messenger__error {
  margin: 0 0 10px;
  color: var(--text);
  font-size: 12px;
}

.messenger :is(button, textarea, a):focus-visible {
  outline: 2px solid var(--text);
  outline-offset: 3px;
}

@media (max-width: 1100px) {
  .messenger {
    grid-template-columns: 200px minmax(0, 1fr);
  }
}

@media (max-width: 850px) {
  .messenger {
    grid-template-columns: minmax(0, 1fr);
  }

  .messenger__sidebar {
    display: none;
  }

  .messenger__back {
    display: inline-flex;
  }
}

@media (max-width: 700px) {
  .messenger {
    height: calc(100dvh - 235px - env(safe-area-inset-bottom));
    min-height: 300px;
    border-radius: 12px;
  }

  .messenger__head {
    min-height: 58px;
    padding: 8px 12px;
  }

  .messenger__messages {
    padding: 14px 10px;
  }

  .messenger__composer {
    padding: 10px;
  }

  .messenger__keyboard,
  .messenger__connection {
    display: none;
  }
}
</style>
