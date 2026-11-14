export const groupRoutes = [
  {
    path: '/groups',
    name: 'groups',
    component: () => import('./pages/GroupsView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/groups/:groupId',
    name: 'group',
    component: () => import('./pages/GroupView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/groups/:groupId/members',
    name: 'group-members',
    component: () => import('./pages/GroupMembersView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
  {
    path: '/groups/:groupId/settings',
    name: 'group-settings',
    component: () => import('./pages/GroupSettingsView.vue'),
    meta: {
      requiresAuth: true,
    },
  },
]
