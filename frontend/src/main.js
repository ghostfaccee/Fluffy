import './assets/main.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import { setSessionExpiredHandler } from './api/client'
import { useAuthStore } from './stores/auth'

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