import './styles/base.css'
import './styles/auth.css'
import './styles/app.css'
import './styles/docs.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { setSessionExpiredHandler } from './api/client'
import { useAuthStore } from './stores/auth'

// Apply the saved theme before Vue renders to avoid a flash of the wrong colors.
const savedTheme = window.localStorage.getItem('fluffy-theme') === 'light' ? 'light' : 'dark'
document.documentElement.dataset.theme = savedTheme
document.documentElement.style.colorScheme = savedTheme

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

setSessionExpiredHandler(() => {
  const auth = useAuthStore(pinia)
  auth.setUser(null)
  const route = router.currentRoute.value
  if (route.meta.requiresAuth) {
    router.push({ name: 'login', query: { redirect: route.fullPath } })
  }
})

app.mount('#app')