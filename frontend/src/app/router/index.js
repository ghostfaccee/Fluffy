import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '@/views/LandingView.vue'
import { useAuthStore } from '@/stores/auth'
import { hasRefreshToken } from '@/api/client'
import { authRoutes } from '@/modules/auth/routes'
import { homeRoutes } from '@/modules/home/routes'
import { chatRoutes } from '@/modules/chat/routes'
import { groupRoutes } from '@/modules/groups/routes'
import { profileRoutes } from '@/modules/profile/routes'
import { settingsRoutes } from '@/modules/settings/routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
    },
    {
      path: '/docs/:page',
      name: 'docs',
      component: () => import('@/views/DocsView.vue'),
      props: true,
    },
    {
      path: '/docs',
      redirect: '/docs/features',
    },

    ...authRoutes,
    ...homeRoutes,
    ...chatRoutes,
    ...groupRoutes,
    ...profileRoutes,
    ...settingsRoutes,
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (!auth.user && hasRefreshToken()) {
    await auth.restoreSession()
  }

  if (to.meta.requiresAuth && !auth.user) {
    return {
      name: 'login',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  if (to.meta.guestOnly && auth.user) {
    return {
      name: 'app',
    }
  }
})

export default router
