<script setup>
import { useAccent } from '@/composables/useAccent'

useAccent()
</script>

<template>
  <div class="fl-root">
    <RouterView />
  </div>
</template>
