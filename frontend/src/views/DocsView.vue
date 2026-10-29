<script setup>
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import LogoIcon from '@/components/LogoIcon.vue'
import { docsNavigation, docsPages } from '@/content/docsContent'

const route = useRoute()
const searchQuery = ref('')
const page = computed(() => docsPages[route.params.page] || docsPages.features)
const activeSlug = computed(() => String(route.params.page || 'features'))
const filteredNavigation = computed(() => {
  const query = searchQuery.value.trim().toLocaleLowerCase('ru')
  if (!query) return docsNavigation
  return docsNavigation.map((group) => ({
    ...group,
    items: group.items.filter((item) => `${item.title} ${item.eyebrow}`.toLocaleLowerCase('ru').includes(query)),
  })).filter((group) => group.items.length)
})
const endpointCount = computed(() => (page.value.endpointGroups || []).reduce((total, group) => total + group.items.length, 0))

function copyPath(path) {
  if (navigator.clipboard?.writeText) navigator.clipboard.writeText(path).catch(() => {})
}
</script>

<template>
  <div class="docs-shell">
    <header class="docs-topbar">
      <RouterLink to="/" class="docs-brand" aria-label="Fluffy — на главную">
        <LogoIcon /><span>Fluffy</span><span class="docs-brand-divider"></span><span class="docs-brand-caption">API Эндпоинты</span>
      </RouterLink>
      <div class="docs-top-actions">
        <RouterLink to="/" class="docs-top-link">Главная</RouterLink>
        <RouterLink to="/register" class="docs-top-cta">Попробовать Fluffy <span aria-hidden="true">↗</span></RouterLink>
      </div>
    </header>

    <div class="docs-layout">
      <aside class="docs-sidebar">
        <label class="docs-search">
          <span aria-hidden="true">⌕</span>
          <input v-model="searchQuery" type="search" placeholder="Найти раздел…" aria-label="Найти раздел документации" />
        </label>
        <nav aria-label="Разделы документации" class="docs-nav">
          <section v-for="group in filteredNavigation" :key="group.label" class="docs-nav-group">
            <h2>{{ group.label }}</h2>
            <RouterLink v-for="item in group.items" :key="item.slug" :to="`/docs/${item.slug}`" class="docs-nav-link" :class="{ active: activeSlug === item.slug }">
              <span class="docs-nav-dot"></span>{{ item.title }}<span v-if="item.slug === 'api'" class="docs-nav-api">API</span>
            </RouterLink>
          </section>
          <p v-if="!filteredNavigation.length" class="docs-no-results">Ничего не найдено. Попробуй другое слово.</p>
        </nav>
        <div class="docs-sidebar-bottom">
          <span class="docs-status-dot"></span>
          <div><strong>Fluffy развивается</strong><small>Эндпоинты могут обновляться вместе с проектом</small></div>
        </div>
      </aside>

      <main class="docs-main">
        <div class="docs-breadcrumb"><RouterLink to="/">Fluffy</RouterLink><span>/</span><span>Эндпоинты</span><span>/</span><strong>{{ page.title }}</strong></div>
        <article class="docs-article">
          <div class="docs-eyebrow"><span class="docs-eyebrow-mark"></span>{{ page.updated }}</div>
          <h1>{{ page.title }}</h1>
          <p class="docs-lead">{{ page.lead }}</p>

          <template v-if="page.endpointGroups">
            <div class="docs-api-intro"><span class="docs-api-icon">{ }</span><div><strong>API v1</strong><p>{{ page.intro }}</p></div></div>
            <div class="docs-api-meta"><span><strong>{{ endpointCount }}</strong> маршрутов</span><span><strong>HTTP + WebSocket</strong> транспорт</span><span><strong>/v1</strong> базовый префикс</span></div>
            <section v-for="group in page.endpointGroups" :key="group.title" class="docs-content-section docs-endpoint-section">
              <div class="docs-section-heading"><h2>{{ group.title }}</h2><span>{{ group.items.length }} {{ group.items.length === 1 ? 'маршрут' : 'маршрутов' }}</span></div>
              <div class="docs-endpoints">
                <div v-for="endpoint in group.items" :key="endpoint[0] + endpoint[1]" class="docs-endpoint">
                  <span class="docs-method" :class="`method-${endpoint[0].toLowerCase()}`">{{ endpoint[0] }}</span>
                  <div class="docs-endpoint-info"><code>{{ endpoint[1] }}</code><p>{{ endpoint[2] }}</p></div>
                  <button class="docs-copy" type="button" :aria-label="`Скопировать ${endpoint[1]}`" title="Скопировать путь" @click="copyPath(endpoint[1])">⧉</button>
                </div>
              </div>
            </section>
          </template>
          <template v-else>
            <section v-for="(section, index) in page.sections" :key="section.title" class="docs-content-section">
              <div class="docs-section-heading"><h2>{{ section.title }}</h2><span v-if="page.sections.length > 1">{{ String(index + 1).padStart(2, '0') }}</span></div>
              <p v-if="section.text" class="docs-section-copy">{{ section.text }}</p>
              <div v-if="section.cards" class="docs-info-grid">
                <article v-for="card in section.cards" :key="card.title" class="docs-info-card"><span class="docs-card-mark"></span><h3>{{ card.title }}</h3><p>{{ card.text }}</p></article>
              </div>
            </section>
            <blockquote v-if="page.quote" class="docs-quote">“{{ page.quote }}”</blockquote>
          </template>

          <div v-if="page.note" class="docs-note"><span class="docs-note-icon">i</span><p>{{ page.note }}</p></div>
          <div v-if="page.links?.length" class="docs-page-links"><a v-for="link in page.links" :key="link.href" :href="link.href" :target="link.external ? '_blank' : undefined" :rel="link.external ? 'noopener noreferrer' : undefined">{{ link.label }} <span aria-hidden="true">↗</span></a></div>
          <div class="docs-page-nav">
            <div><span>Наш проект</span><strong>Спокойное общение, открытая разработка</strong></div>
            <RouterLink :to="activeSlug === 'api' ? '/docs/opensource' : '/docs/api'">{{ activeSlug === 'api' ? 'Об Open Source' : 'API Эндпоинты' }} <span aria-hidden="true">→</span></RouterLink>
          </div>
        </article>
        <footer class="docs-footer"><span>© {{ new Date().getFullYear() }} Fluffy Project</span><div><RouterLink to="/docs/principles">Принципы</RouterLink><RouterLink to="/docs/opensource">Open Source</RouterLink><a href="mailto:fluffy.social.network@gmail.com">Связаться</a></div></footer>
      </main>
    </div>
  </div>
</template>
