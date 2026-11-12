export const docsRoutes = [
  {
    path: '/docs/:page',
    name: 'docs',
    component: () => import('./pages/DocsView.vue'),
    props: true,
  },
  {
    path: '/docs',
    redirect: '/docs/features',
  },
]
