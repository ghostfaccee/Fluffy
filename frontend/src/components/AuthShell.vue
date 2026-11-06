<script setup>
import LogoIcon from '@/components/LogoIcon.vue'
</script>

<template>
  <div class="auth-page">
    <header class="auth-header">
      <div class="container">
        <RouterLink to="/" class="logo" aria-label="Fluffy — на главную">
          <LogoIcon />
          <span class="logo-name">Fluffy</span>
        </RouterLink>
      </div>
    </header>

    <main class="auth-main">
      <slot />
    </main>
  </div>
</template>