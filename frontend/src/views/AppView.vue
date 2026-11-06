<script setup>
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/AppShell.vue'

const auth = useAuthStore()
const user = computed(() => auth.user)
</script>

<template>
  <AppShell>
    <div class="container">
      <section class="app-section app-section--hero">
        <h1 class="app-title app-title--hero">
          Добро пожаловать,<br>
          <span class="gradient-text">{{ user?.name || user?.username }}.</span>
        </h1>
        <p class="app-welcome">
          Твоё пространство для общения, новых знакомств и своих компаний. Напиши друзьям или собери всех в одной группе.
        </p>
      </section>

      <section class="home-shortcuts" aria-label="Быстрые действия">
        <RouterLink to="/chats" class="home-shortcut home-shortcut--messages">
          <span class="home-shortcut-icon" aria-hidden="true">↗</span>
          <span class="home-shortcut-copy">
            <strong>Личные сообщения</strong>
            <span>Продолжи разговор один на один</span>
          </span>
          <span class="home-shortcut-arrow" aria-hidden="true">→</span>
        </RouterLink>
        <RouterLink to="/groups" class="home-shortcut home-shortcut--groups">
          <span class="home-shortcut-icon" aria-hidden="true">✳</span>
          <span class="home-shortcut-copy">
            <strong>Твои группы</strong>
            <span>Общайтесь вместе и делитесь идеями</span>
          </span>
          <span class="home-shortcut-arrow" aria-hidden="true">→</span>
        </RouterLink>
        <RouterLink to="/me" class="home-shortcut home-shortcut--profile">
          <span class="home-shortcut-icon" aria-hidden="true">◉</span>
          <span class="home-shortcut-copy">
            <strong>Твой профиль</strong>
            <span>Расскажи немного о себе</span>
          </span>
          <span class="home-shortcut-arrow" aria-hidden="true">→</span>
        </RouterLink>
      </section>

      <section class="home-note">
        <span class="home-note-mark" aria-hidden="true"></span>
        <div>
          <h2>Хорошо, что ты здесь.</h2>
          <p>Fluffy — место, где поддерживать связь просто. Найди человека через поиск в шапке или начни с группы.</p>
        </div>
      </section>
    </div>
  </AppShell>
</template>