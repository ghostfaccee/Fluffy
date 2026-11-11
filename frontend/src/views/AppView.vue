<script setup>
import AppShell from '@/components/AppShell.vue'
</script>

<template>
  <AppShell>
    <section class="home-page">
      <h1 class="home-page__title">Главная</h1>

      <p class="home-page__description">
        Добро пожаловать во Fluffy. Откройте свой профиль,
        продолжите переписку или загляните в группы.
      </p>

      <nav class="home-page__links" aria-label="Быстрые переходы">
        <RouterLink :to="{ name: 'me' }" class="home-link">
          <strong>Мой профиль</strong>
          <span>Информация о вас и ваши публикации</span>
        </RouterLink>

        <RouterLink :to="{ name: 'chats' }" class="home-link">
          <strong>Сообщения</strong>
          <span>Ваши диалоги и переписки</span>
        </RouterLink>

        <RouterLink :to="{ name: 'groups' }" class="home-link">
          <strong>Группы</strong>
          <span>Общение в сообществах</span>
        </RouterLink>

        <RouterLink :to="{ name: 'settings' }" class="home-link">
          <strong>Настройки</strong>
          <span>Тема оформления и цвет акцента</span>
        </RouterLink>
      </nav>
    </section>
  </AppShell>
</template>

<style scoped>
.home-page {
  min-width: 0;
}

.home-page__title {
  margin: 0 0 10px;
  color: var(--text);
  font-size: 24px;
  font-weight: 650;
  letter-spacing: -0.5px;
}

.home-page__description {
  max-width: 540px;
  margin: 0 0 24px;
  color: var(--muted);
  font-size: 14px;
  line-height: 1.7;
}

.home-page__links {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.home-link {
  display: grid;
  gap: 8px;
  min-width: 0;
  padding: 22px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-card);
  color: var(--text);
  text-decoration: none;
  transition:
    border-color 150ms ease,
    box-shadow 150ms ease;
}

.home-link:hover {
  border-color: var(--accent);
  box-shadow: inset 3px 0 0 var(--accent);
}

.home-link:focus-visible {
  outline: 2px solid var(--text);
  outline-offset: 4px;
}

.home-link strong {
  font-size: 16px;
  font-weight: 600;
}

.home-link span {
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 600px) {
  .home-page__links {
    grid-template-columns: minmax(0, 1fr);
  }

  .home-link {
    padding: 18px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .home-link {
    transition: none;
  }
}
</style>
