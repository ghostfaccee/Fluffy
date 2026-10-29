import { ref, watch } from 'vue'

const STORAGE_KEY = 'fluffy-theme'
const initialTheme = typeof window !== 'undefined'
  ? (window.localStorage.getItem(STORAGE_KEY) === 'light' ? 'light' : 'dark')
  : 'dark'

const theme = ref(initialTheme)

function applyTheme(value) {
  if (typeof document !== 'undefined') {
    document.documentElement.dataset.theme = value
    document.documentElement.style.colorScheme = value
  }
  if (typeof window !== 'undefined') {
    window.localStorage.setItem(STORAGE_KEY, value)
  }
}

applyTheme(theme.value)
watch(theme, applyTheme)

export function useTheme() {
  function setTheme(value) {
    if (value === 'dark' || value === 'light') theme.value = value
  }

  return { theme, setTheme }
}
