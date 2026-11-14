export const profileRoutes = [
  {
    path: '/me',
    name: 'me',
    component: () => import('./pages/MeView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/users/:username',
    name: 'user',
    component: () => import('./pages/UserProfileView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
]
