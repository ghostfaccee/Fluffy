<script setup>
import { computed, ref } from 'vue'
import { useChatStore } from '@/stores/chat'
import AppShell from '@/components/AppShell.vue'
import ChatListItem from '@/components/ChatListItem.vue'

const chat = useChatStore()
const search = ref('')

const list = computed(() => {
  const query = search.value.trim().toLocaleLowerCase()

  return chat.visibleConversations.filter((conversation) =>
    !query || [conversation.name, conversation.username]
      .some((value) => String(value || '').toLocaleLowerCase().includes(query)),
  )
})
</script>

<template>
  <AppShell>
    <section class="dialogs">
      <header class="dialogs__head">
        <input
          v-model="search"
          type="search"
          placeholder="Найти диалог"
          aria-label="Поиск по диалогам"
          autocomplete="off"
        />
      </header>

      <div v-if="list.length" class="dialogs__list">
        <ChatListItem
          v-for="conversation in list"
          :key="conversation.user_id"
          :conversation="conversation"
        />
      </div>

      <div v-else class="dialogs__empty">
        <strong>
          {{ search.trim() ? 'Ничего не найдено' : 'Ваши разговоры — здесь' }}
        </strong>
        <p>
          {{ search.trim()
            ? 'Попробуйте другое имя или логин.'
            : 'Найдите пользователя через верхний поиск и откройте его профиль, чтобы написать.' }}
        </p>
      </div>
    </section>
  </AppShell>
</template>

<style scoped>
.dialogs {
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-card);
}

.dialogs__head {
  padding: 16px;
  border-bottom: 1px solid var(--border);
}

.dialogs__head input {
  box-sizing: border-box;
  width: 100%;
  padding: 11px 13px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
  color: var(--text);
  font: inherit;
  font-size: 13px;
}

.dialogs__head input:focus-visible {
  outline: 2px solid var(--text);
  outline-offset: 3px;
}

.dialogs__list {
  display: grid;
  gap: 4px;
  padding: 8px;
}

.dialogs__list :deep(a) {
  border-radius: 10px;
}

.dialogs__empty {
  padding: 48px 24px;
  text-align: center;
}

.dialogs__empty strong {
  color: var(--text);
  font-size: 17px;
  font-weight: 600;
}

.dialogs__empty p {
  max-width: 380px;
  margin: 10px auto 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
}
</style>
