<script setup>
import { computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import AppShell from '@/components/AppShell.vue'
import ChatListItem from '@/components/ChatListItem.vue'

const chat = useChatStore()
const list = computed(() => chat.visibleConversations)
</script>

<template>
  <AppShell>
    <div class="container">

      <div class="chats-layout">
        <aside class="chats-sidebar">
          <p v-if="!list.length" class="app-hint">
            Пока нет диалогов. Найди пользователя через поиск и нажми «Написать».
          </p>
          <ChatListItem
            v-for="c in list"
            :key="c.user_id"
            :conversation="c"
          />
        </aside>

        <div class="chats-placeholder">
          <p class="app-hint">Выбери диалог слева, чтобы открыть переписку.</p>
        </div>
      </div>
    </div>
  </AppShell>
</template>