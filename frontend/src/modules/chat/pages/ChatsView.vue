<script setup>
import { computed, ref } from 'vue'
import { useChatStore } from '@/modules/chat/stores/chat'
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

<style scoped src="../styles/dialogs.css"></style>
