export const chatRoutes = [
  {
    path: '/chats',
    name: 'chats',
    component: () => import('./pages/ChatsView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/chats/:userId',
    name: 'chat',
    component: () => import('./pages/ChatView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
]
