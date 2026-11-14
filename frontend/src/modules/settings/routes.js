export const settingsRoutes = [
  {
    path: '/settings',
    name: 'settings',
    component: () => import('./pages/SettingsView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
]
