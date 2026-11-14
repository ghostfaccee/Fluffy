export const authRoutes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('./pages/LoginView.vue'),
    meta: {
      guestOnly: true,
    },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('./pages/RegisterView.vue'),
    meta: {
      guestOnly: true,
    },
  },
  {
    path: '/verify-email',
    name: 'verify-email',
    component: () => import('./pages/VerifyEmailView.vue'),
  },
]
