<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import LogoIcon from '@/components/LogoIcon.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import AppFooter from '@/components/AppFooter.vue'

const auth = useAuthStore()
const router = useRouter()

const user = computed(() => auth.user)
const searchQuery = ref('')
const dropdownOpen = ref(false)

function onSearch() {
  const q = searchQuery.value.trim()
  if (!q) return
  if (q === user.value?.username) router.push({ name: 'me' })
  else router.push({ name: 'user', params: { username: q } })
  searchQuery.value = ''
}

async function logout() {
  dropdownOpen.value = false
  await auth.logout()
  router.push({ name: 'landing' })
}

function toggleDropdown() {
  dropdownOpen.value = !dropdownOpen.value
}

function closeDropdown() {
  dropdownOpen.value = false
}

function onDocumentClick(e) {
  if (!e.target.closest('.shell-user')) dropdownOpen.value = false
}

function onKeydown(e) {
  if (e.key === 'Escape') dropdownOpen.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="shell">
    <header class="shell-header">
      <div class="container shell-header-inner">
        <RouterLink to="/app" class="logo" aria-label="Fluffy — главная">
          <LogoIcon />
          <span class="logo-name">Fluffy</span>
        </RouterLink>

        <form class="shell-search" @submit.prevent="onSearch">
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Найти пользователя"
            autocomplete="off"
          />
        </form>

        <div class="shell-actions">
          <div class="shell-user">
            <button
              class="shell-avatar-btn"
              type="button"
              :aria-expanded="dropdownOpen"
              aria-label="Меню пользователя"
              @click="toggleDropdown"
            >
              <UserAvatar :user="user" :size="34" />
            </button>

            <div class="shell-dropdown" :class="{ open: dropdownOpen }">
              <RouterLink to="/me" class="shell-dropdown-item" @click="closeDropdown">
                Мой профиль
              </RouterLink>
              <RouterLink to="/settings" class="shell-dropdown-item" @click="closeDropdown">
                Настройки
              </RouterLink>
              <button class="shell-dropdown-item shell-dropdown-item--danger" type="button" @click="logout">
                Выйти
              </button>
            </div>
          </div>
        </div>
      </div>
    </header>

    <main class="shell-main">
      <slot />
    </main>

    <AppFooter />
  </div>
</template>