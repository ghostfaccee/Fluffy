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
          Тихое место в шумной сети. Здесь ты сам решаешь, что заслуживает твоего внимания.
        </p>
      </section>
    </div>
  </AppShell>
</template>