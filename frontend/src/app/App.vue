<script setup>
import { useAccent } from '@/shared/composables/useAccent'

useAccent()
</script>

<template>
  <div class="fl-root">
    <RouterView />
  </div>
</template>
