<script setup>
defineProps({
  name: {
    type: String,
    required: true,
  },
  size: {
    type: Number,
    default: 22,
  },
})

const paths = {
  home: ['m3 10 9-7 9 7', 'M5 9v12h5v-7h4v7h5V9'],
  user: [
    'M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
    'M4 21v-2a8 8 0 0 1 16 0v2',
  ],
  chat: [
    'M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2v-10A8.5 8.5 0 0 1 10.5 3h2A8.5 8.5 0 0 1 21 11.5Z',
    'M7 10h9M7 14h6',
  ],
  groups: [
    'M15 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0',
    'M3 21v-2a8 8 0 0 1 16 0v2',
    'M18 4a4 4 0 0 1 0 8M22 21v-2a8 8 0 0 0-3-6',
  ],
  settings: [
    'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8',
    'm9 3-1 3-3 1-2 3 2 2-1 3 2 3 3-1 2 3h3l1-3 3-1 2-3-2-2 1-3-2-3-3 1-2-3Z',
  ],
  search: ['M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0', 'm15 15 6 6'],
  logout: ['M9 4H4v16h5M9 12h12m-4-4 4 4-4 4'],
  arrow: ['m9 5 7 7-7 7'],
}
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.7"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
    focusable="false"
  >
    <path v-for="(path, index) in paths[name] || []" :key="index" :d="path" />
  </svg>
</template>