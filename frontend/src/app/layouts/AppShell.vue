<script setup>
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/modules/auth/stores/auth'
import { useWsStore } from '@/shared/stores/ws'
import { useChatStore } from '@/modules/chat/stores/chat'
import { useMessagingRealtime } from '@/app/composables/useMessagingRealtime.js'
import LogoIcon from '@/shared/ui/LogoIcon.vue'
import UserAvatar from '@/shared/ui/UserAvatar.vue'
import AppIcon from '@/shared/ui/AppIcon.vue'

const auth = useAuthStore()
const ws = useWsStore()
const chat = useChatStore()
const route = useRoute()
const router = useRouter()

useMessagingRealtime()

const searchQuery = ref('')
const loggingOut = ref(false)
const searchError = ref('')

const user = computed(() => auth.user)

const unreadTotal = computed(() =>
  chat.conversations.reduce((sum, conversation) => {
    const unread = Number(conversation.unread)

    return sum + (
      Number.isFinite(unread)
        ? Math.max(0, unread)
        : 0
    )
  }, 0),
)

const navigation = [
  { name: 'app', label: 'Главная', icon: 'home' },
  { name: 'me', label: 'Мой профиль', icon: 'user' },
  { name: 'chats', label: 'Сообщения', icon: 'chat' },
  { name: 'groups', label: 'Группы', icon: 'groups' },
  { name: 'settings', label: 'Настройки', icon: 'settings' },
]

const title = computed(() => {
  if (route.name === 'user') {
    return 'Профиль пользователя'
  }

  if (['chat', 'chats'].includes(route.name)) {
    return 'Сообщения'
  }

  if (String(route.name).startsWith('group')) {
    return 'Группы'
  }

  return navigation.find(
    (item) => item.name === route.name,
  )?.label || 'Fluffy'
})

function isActive(name) {
  if (name === 'chats') {
    return ['chats', 'chat'].includes(route.name)
  }

  if (name === 'groups') {
    return String(route.name).startsWith('group')
  }

  return route.name === name
}

async function onSearch() {
  const username = searchQuery.value.trim().replace(/^@/, '')

  if (!username) return

  searchError.value = ''

  try {
    if (username === user.value?.username) {
      await router.push({ name: 'me' })
    } else {
      await router.push({
        name: 'user',
        params: { username },
      })
    }

    searchQuery.value = ''
  } catch {
    searchError.value =
      'Не удалось открыть профиль. Попробуйте ещё раз.'
  }
}

async function logout() {
  if (loggingOut.value) return

  loggingOut.value = true

  try {
    ws.disconnect()
    await auth.logout()
    await router.push({ name: 'landing' })
  } finally {
    loggingOut.value = false
  }
}
</script>

<template>
  <div class="fl-shell">
    <header class="fl-header">
      <div class="fl-header__inner">
        <RouterLink
          :to="{ name: 'app' }"
          class="fl-brand"
          aria-label="Fluffy — главная"
        >
          <LogoIcon />
          <span>Fluffy<span class="fl-brand__dot">.</span></span>
        </RouterLink>

        <form
          class="fl-search"
          role="search"
          @submit.prevent="onSearch"
        >
          <AppIcon name="search" :size="19" />

          <input
            v-model="searchQuery"
            type="search"
            aria-label="Поиск пользователя по логину"
            placeholder="Найти по @username"
            autocomplete="off"
            maxlength="100"
            @input="searchError = ''"
          />

          <button
            type="submit"
            aria-label="Найти пользователя"
          >
            <AppIcon name="arrow" :size="18" />
          </button>

          <span
            v-if="searchError"
            class="fl-search__error"
            role="alert"
          >
            {{ searchError }}
          </span>
        </form>

        <RouterLink
          :to="{ name: 'me' }"
          class="fl-account"
        >
          <UserAvatar :user="user" :size="36" />
          <span>
            {{ user?.name || user?.username || 'Мой профиль' }}
          </span>
        </RouterLink>
      </div>
    </header>

    <div class="fl-layout">
      <aside class="fl-sidebar">
        <nav
          class="fl-nav"
          aria-label="Основная навигация"
        >
          <RouterLink
            v-for="item in navigation"
            :key="item.name"
            :to="{ name: item.name }"
            class="fl-nav__item"
            :class="{ 'is-active': isActive(item.name) }"
            :aria-current="isActive(item.name) ? 'page' : undefined"
          >
            <span class="fl-nav__icon">
              <AppIcon :name="item.icon" />

              <span
                v-if="item.name === 'chats' && unreadTotal"
                class="fl-mobile-dot"
                aria-hidden="true"
              />
            </span>

            <span class="fl-nav__label">
              {{ item.label }}
            </span>

            <span
              v-if="item.name === 'chats' && unreadTotal"
              class="fl-badge"
            >
              <span class="fl-sr-only">
                Непрочитанных сообщений:
              </span>
              {{ unreadTotal > 99 ? '99+' : unreadTotal }}
            </span>
          </RouterLink>
        </nav>

        <div class="fl-sidebar__bottom">
          <button
            class="fl-logout"
            type="button"
            :disabled="loggingOut"
            @click="logout"
          >
            <AppIcon name="logout" :size="20" />
            {{ loggingOut ? 'Выходим…' : 'Выйти из аккаунта' }}
          </button>

          <RouterLink
            to="/docs/features"
            class="fl-help"
          >
            О проекте и возможностях
          </RouterLink>
        </div>
      </aside>

      <main id="main-content" class="fl-content">
        <div class="fl-page-heading">
          <div>
            <span class="fl-eyebrow">ВАШЕ ПРОСТРАНСТВО</span>
            <h1>{{ title }}</h1>
          </div>

          <span
            class="fl-page-heading__mark"
            aria-hidden="true"
          >
            &#10022;
          </span>
        </div>

        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.fl-shell {
  --fluffy-accent: var(--green, #42c99a);
  --fluffy-on-accent: #10241e;
  min-height: 100dvh;
  background: var(--bg);
  color: var(--text);
}

.fl-header {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 72px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border);
}

.fl-header__inner {
  display: grid;
  grid-template-columns: 224px minmax(180px, 480px) 1fr;
  align-items: center;
  gap: 24px;
  width: min(1320px, calc(100% - 48px));
  height: 100%;
  margin: auto;
}

.fl-brand {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  width: fit-content;
  font-size: 26px;
  font-weight: 750;
  letter-spacing: -1px;
}

.fl-brand :deep(svg),
.fl-brand :deep(img) {
  width: 34px;
  height: 34px;
}

.fl-brand__dot {
  color: var(--fluffy-accent);
}

.fl-search {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  height: 42px;
  padding: 0 10px 0 14px;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg);
  color: var(--muted);
}

.fl-search:focus-within {
  border-color: var(--fluffy-accent);
}

.fl-search input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--text);
  font: inherit;
  font-size: 13px;
}

.fl-search input::placeholder {
  color: var(--muted);
}

.fl-search button {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: 0;
  border-radius: 7px;
  background: var(--bg-soft);
  color: var(--text);
  cursor: pointer;
}

.fl-search__error {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  right: 0;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg-card);
  color: var(--text);
  font-size: 12px;
}

.fl-account {
  display: flex;
  align-items: center;
  justify-self: end;
  gap: 10px;
  min-width: 0;
  max-width: 220px;
  font-size: 13px;
  font-weight: 600;
}

.fl-account > span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fl-layout {
  display: grid;
  grid-template-columns: 224px minmax(0, 1fr);
  align-items: start;
  gap: 24px;
  width: min(1320px, calc(100% - 48px));
  margin: 0 auto;
}

.fl-sidebar {
  position: sticky;
  top: 96px;
  display: flex;
  flex-direction: column;
  min-height: calc(100dvh - 120px);
  padding: 0 8px 20px 0;
  margin-top: 24px;
}

.fl-nav {
  display: grid;
  gap: 5px;
}

.fl-nav__item {
  display: flex;
  align-items: center;
  gap: 13px;
  min-height: 48px;
  padding: 10px 14px;
  border-radius: 12px;
  color: var(--muted);
  font-size: 14px;
  font-weight: 550;
  transition: background 150ms, color 150ms;
}

.fl-nav__item:hover {
  background: var(--bg-soft);
  color: var(--text);
}

.fl-nav__item.is-active {
  background: color-mix(
    in srgb,
    var(--fluffy-accent) 12%,
    transparent
  );
  color: var(--fluffy-accent);
}

.fl-nav__icon {
  position: relative;
  display: flex;
  flex-shrink: 0;
}

.fl-badge {
  min-width: 23px;
  padding: 1px 6px;
  margin-left: auto;
  border-radius: 7px;
  background: var(--fluffy-accent);
  color: var(--fluffy-on-accent);
  text-align: center;
  font-size: 11px;
  font-weight: 750;
}

.fl-mobile-dot {
  display: none;
}

.fl-sidebar__bottom {
  display: grid;
  gap: 15px;
  padding: 24px 14px 0;
  margin-top: auto;
}

.fl-logout {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border: 0;
  background: transparent;
  color: var(--muted);
  text-align: left;
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}

.fl-logout:hover,
.fl-help:hover {
  color: var(--text);
}

.fl-logout:disabled {
  opacity: 0.5;
  cursor: wait;
}

.fl-help {
  color: var(--muted);
  font-size: 11px;
}

.fl-content {
  min-width: 0;
  padding: 28px 0 48px;
}

.fl-page-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.fl-eyebrow {
  color: var(--muted);
  font-size: 10px;
  font-weight: 650;
  letter-spacing: 1.8px;
}

.fl-page-heading h1 {
  margin: 3px 0 0;
  font-size: 27px;
  font-weight: 700;
  line-height: 1.3;
  letter-spacing: -0.8px;
}

.fl-page-heading__mark {
  color: var(--fluffy-accent);
  font-size: 32px;
}

.fl-content :deep(.container) {
  width: 100%;
  max-width: none;
  margin: 0;
}

.fl-content :deep(.app-section) {
  border-radius: 18px;
}

.fl-shell :is(a, button):focus-visible {
  outline: 2px solid var(--fluffy-accent);
  outline-offset: 4px;
}

.fl-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip-path: inset(50%);
  white-space: nowrap;
}

@media (max-width: 1000px) {
  .fl-header__inner {
    grid-template-columns: 190px minmax(160px, 1fr) auto;
  }

  .fl-layout {
    grid-template-columns: 190px minmax(0, 1fr);
  }

  .fl-account > span {
    display: none;
  }
}

@media (max-width: 700px) {
  .fl-header {
    height: 64px;
  }

  .fl-header__inner {
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 12px;
    width: calc(100% - 28px);
  }

  .fl-brand {
    font-size: 22px;
  }

  .fl-brand :deep(svg),
  .fl-brand :deep(img) {
    display: none;
  }

  .fl-search {
    gap: 7px;
    height: 38px;
    padding-left: 10px;
  }

  .fl-search input {
    font-size: 12px;
  }

  .fl-layout {
    display: block;
    width: calc(100% - 28px);
  }

  .fl-sidebar {
    position: fixed;
    inset: auto 0 0;
    top: auto;
    z-index: 110;
    min-height: 0;
    padding: 6px 6px calc(6px + env(safe-area-inset-bottom));
    margin: 0;
    border-top: 1px solid var(--border);
    background: var(--bg-card);
  }

  .fl-nav {
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 3px;
  }

  .fl-nav__item {
    flex-direction: column;
    justify-content: center;
    gap: 4px;
    min-height: 52px;
    padding: 6px 2px;
    border-radius: 10px;
    font-size: 9px;
  }

  .fl-nav__label {
    white-space: nowrap;
  }

  .fl-badge,
  .fl-sidebar__bottom {
    display: none;
  }

  .fl-mobile-dot {
    position: absolute;
    top: -2px;
    right: -3px;
    display: block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--fluffy-accent);
  }

  .fl-content {
    padding-top: 20px;
    padding-bottom: calc(100px + env(safe-area-inset-bottom));
  }

  .fl-page-heading {
    margin-bottom: 18px;
  }

  .fl-page-heading h1 {
    font-size: 23px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .fl-nav__item {
    transition: none;
  }
}

.fl-nav {
  gap: 4px;
}

.fl-nav__item {
  min-height: 40px;
  padding: 8px 12px;
  gap: 11px;
  font-size: 13px;
  border-radius: 10px;
}

.fl-content {
  padding-top: 22px;
}

.fl-page-heading {
  margin-bottom: 18px;
}

.fl-page-heading h1 {
  font-size: 23px;
}

.fl-eyebrow {
  font-size: 9px;
  letter-spacing: 1.4px;
}

.fl-page-heading__mark {
  font-size: 26px;
}

.fl-content :deep(.app-section) {
  margin-bottom: 24px;
}

.fl-content :deep(.app-profile-row) {
  grid-template-columns: max-content minmax(0, 1fr);
  align-items: start;
  gap: 20px;
}

.fl-content :deep(.app-profile-info) {
  min-width: 0;
}

@media (max-width: 700px) {
  .fl-nav__item {
    min-height: 48px;
    padding: 5px 2px;
    gap: 4px;
    font-size: 9px;
  }

  .fl-content {
    padding-top: 18px;
  }

  .fl-page-heading h1 {
    font-size: 21px;
  }

  .fl-content :deep(.app-profile-row) {
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
  }
}
</style>
