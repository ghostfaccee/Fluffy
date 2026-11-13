<script setup>
import {
  ref,
  computed,
  watch,
  nextTick,
  onMounted,
  onBeforeUnmount,
} from 'vue'
import { useRoute } from 'vue-router'
import { useChatStore } from '@/modules/chat/stores/chat'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { useWsStore } from '@/shared/stores/ws'
import AppShell from '@/app/layouts/AppShell.vue'
import ChatListItem from '@/modules/chat/components/ChatListItem.vue'
import MessageBubble from '@/modules/chat/components/MessageBubble.vue'

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
  conversations.value.find(
    (conversation) =>
      String(conversation.user_id) === String(userId.value),
  ),
)

let mounted = false
let syncIntervalId = null
let unsubscribeReconnect = null
let stopRouteWatch = null

function isCurrentVisible(id) {
  return (
    mounted &&
    route.name === 'chat' &&
    String(userId.value) === String(id) &&
    !document.hidden
  )
}

async function scrollToBottom() {
  await nextTick()

  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

async function readVisibleChat() {
  const id = userId.value

  if (!id || !isCurrentVisible(id)) return

  // Сначала даем Vue отрисовать загруженные сообщения.
  await nextTick()

  if (!isCurrentVisible(id)) return

  try {
    await chat.markRead(id)
  } catch (cause) {
    // Счетчик не сбрасывается при неудачном запросе.
    // Повтор произойдет при синхронизации или возврате во вкладку.
    console.error('Failed to mark messages as read:', cause)
  }
}

async function openChat(id) {
  if (!id || !mounted) return

  if (String(id) === String(auth.user?.user_id)) {
    error.value = 'Нельзя открыть чат с самим собой.'
    return
  }

  error.value = ''

  try {
    await chat.loadChat(id)

    if (!mounted || String(userId.value) !== String(id)) return

    await scrollToBottom()
    await readVisibleChat()
  } catch (cause) {
    if (!mounted || String(userId.value) !== String(id)) return

    error.value =
      cause?.status === 404
        ? 'Пользователь не найден.'
        : 'Не удалось загрузить историю.'
  }
}

async function syncCurrentChat() {
  const id = userId.value

  if (!id || !isCurrentVisible(id)) return

  try {
    await chat.loadChat(id)

    if (!isCurrentVisible(id)) return

    await readVisibleChat()
  } catch (cause) {
    console.error('Failed to synchronize chat:', cause)
  }
}

async function send() {
  const content = text.value.trim()
  const receiverId = userId.value

  if (!content || sending.value) return

  sending.value = true
  error.value = ''

  try {
    await chat.sendMessage(receiverId, content)

    if (
      mounted &&
      String(userId.value) === String(receiverId)
    ) {
      text.value = ''
      await scrollToBottom()
    }
  } catch {
    if (String(userId.value) === String(receiverId)) {
      error.value = 'Не удалось отправить сообщение.'
    }
  } finally {
    sending.value = false
  }
}

function onKeydown(event) {
  if (
    event.key === 'Enter' &&
    !event.shiftKey &&
    !event.isComposing
  ) {
    event.preventDefault()
    void send()
  }
}

function onVisibilityChange() {
  if (!document.hidden) {
    void syncCurrentChat()
  }
}

function onWindowFocus() {
  void syncCurrentChat()
}

onMounted(() => {
  mounted = true

  unsubscribeReconnect = ws.on('connected', () => {
    void syncCurrentChat()
  })

  document.addEventListener(
    'visibilitychange',
    onVisibilityChange,
  )

  window.addEventListener('focus', onWindowFocus)

  stopRouteWatch = watch(
    () => route.params.userId,
    (id) => {
      text.value = ''
      void openChat(id)
    },
    { immediate: true },
  )

  // Сервер не присылает WS-событие о прочтении.
  // Сверяем историю и галочки только в видимом диалоге.
  syncIntervalId = window.setInterval(() => {
    void syncCurrentChat()
  }, 10000)
})

onBeforeUnmount(() => {
  mounted = false

  stopRouteWatch?.()
  unsubscribeReconnect?.()

  if (syncIntervalId != null) {
    window.clearInterval(syncIntervalId)
  }

  document.removeEventListener(
    'visibilitychange',
    onVisibilityChange,
  )

  window.removeEventListener('focus', onWindowFocus)
})

watch(
  () => current.value.messages.length,
  async () => {
    if (!mounted) return

    await scrollToBottom()
    await readVisibleChat()
  },
  { flush: 'post' },
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
          <p
            v-if="!conversations.length"
            class="messenger__hint"
          >
            Здесь появятся ваши переписки.
          </p>

          <ChatListItem
            v-for="conversation in conversations"
            :key="conversation.user_id"
            :conversation="conversation"
            :active="String(conversation.user_id) === String(userId)"
          />
        </div>
      </aside>

      <section
        class="messenger__panel"
        aria-label="Переписка"
      >
        <header class="messenger__head">
          <RouterLink
            :to="{ name: 'chats' }"
            class="messenger__back"
            aria-label="Вернуться к диалогам"
          >
            Назад
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
            {{ ws.connected ? 'На связи' : 'Подключение...' }}
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
            Загружаем переписку...
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

        <form
          class="messenger__composer"
          @submit.prevent="send"
        >
          <p
            v-if="error"
            class="messenger__error"
            role="alert"
          >
            {{ error }}
          </p>

          <div class="messenger__input-row">
            <textarea
              v-model="text"
              class="messenger__textarea"
              rows="2"
              placeholder="Написать сообщение..."
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
              {{ sending ? '...' : '↑' }}
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
