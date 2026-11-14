export const homeRoutes = [
  {
    path: '/app',
    name: 'app',
    component: () => import('./pages/AppView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
]
