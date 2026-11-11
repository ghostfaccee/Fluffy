import '@/app/styles/index.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from '@/app/App.vue'
import router from '@/app/router'
import { setSessionExpiredHandler } from '@/api/client'
import { useAuthStore } from '@/stores/auth'

// Применяем сохранённую тему до первого рендера Vue.
const savedTheme =
  window.localStorage.getItem('fluffy-theme') === 'light'
    ? 'light'
    : 'dark'

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
    router.push({
      name: 'login',
      query: { redirect: route.fullPath },
    })
  }
})

app.mount('#app')
