(() => {
  'use strict'

  const NS = 'http://www.w3.org/2000/svg'
  const root = document.documentElement

  const PATHS = {
    arrow: [
      'M7 17 17 7',
      'M7 7h10v10',
    ],
    code: [
      'm8 7-5 5 5 5',
      'm16 7 5 5-5 5',
      'm14 4-4 16',
    ],
    book: [
      'M12 7v14',
      'M3 3h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5v17h-5a4 4 0 0 0-4 1 4 4 0 0 0-4-1H3Z',
    ],
    chat: [
      'M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a9.5 9.5 0 0 1 19 0Z',
      'M7 10h10',
      'M7 14h6',
    ],
    users: [
      'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2',
      'M16 3a4 4 0 0 1 0 8',
      'M22 21v-2a4 4 0 0 0-3-3.87',
    ],
    user: [
      'M20 21v-2a7 7 0 0 0-14 0v2',
      'M13 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
    ],
    layers: [
      'm12 3 10 6-10 6L2 9Z',
      'm2 13 10 6 10-6',
      'm2 17 10 6 10-6',
    ],
    shield: [
      'M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z',
      'm9 12 2 2 4-4',
    ],
    server: [
      'M4 3h16v7H4Z',
      'M4 14h16v7H4Z',
      'M7 6.5h.01',
      'M7 17.5h.01',
    ],
    sun: [
      'M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8Z',
      'M12 2v2',
      'M12 20v2',
      'M2 12h2',
      'M20 12h2',
      'm4.93 4.93 1.42 1.42',
      'm17.65 17.65 1.42 1.42',
      'm4.93 19.07 1.42-1.42',
      'm17.65 6.35 1.42-1.42',
    ],
    moon: [
      'M20.9 13a9 9 0 0 1-9.9-9.9A9 9 0 1 0 20.9 13Z',
    ],
    menu: [
      'M4 6h16',
      'M4 12h16',
      'M4 18h16',
    ],
    close: [
      'm6 6 12 12',
      'M6 18 18 6',
    ],
    left: [
      'M19 12H5',
      'm12 19-7-7 7-7',
    ],
    right: [
      'M5 12h14',
      'm12 5 7 7-7 7',
    ],
    zoom: [
      'M10 3a7 7 0 1 0 0 14 7 7 0 0 0 0-14Z',
      'm15 15 6 6',
      'M7 10h6',
      'M10 7v6',
    ],
    check: [
      'm5 12 4 4L19 6',
    ],
  }

  function icon(name) {
    const svg = document.createElementNS(NS, 'svg')

    svg.classList.add('fl-icon')
    svg.setAttribute('viewBox', '0 0 24 24')
    svg.setAttribute('fill', 'none')
    svg.setAttribute('stroke', 'currentColor')
    svg.setAttribute('stroke-width', '1.7')
    svg.setAttribute('stroke-linecap', 'round')
    svg.setAttribute('stroke-linejoin', 'round')
    svg.setAttribute('aria-hidden', 'true')
    svg.setAttribute('focusable', 'false')

    for (const d of PATHS[name] || PATHS.code) {
      const path = document.createElementNS(NS, 'path')
      path.setAttribute('d', d)
      svg.append(path)
    }

    if (name === 'users') {
      const circle = document.createElementNS(NS, 'circle')
      circle.setAttribute('cx', '9')
      circle.setAttribute('cy', '7')
      circle.setAttribute('r', '4')
      svg.append(circle)
    }

    return svg
  }

  function node(tag, className, text) {
    const result = document.createElement(tag)

    if (className) result.className = className
    if (text !== undefined) result.textContent = text

    return result
  }

    function replaceIcon(target, name) {
    if (!target) return

    const existing = target.firstElementChild

    if (
      target.dataset.flIcon === name &&
      target.childNodes.length === 1 &&
      existing?.matches('svg.fl-icon')
    ) {
      return
    }

    target.replaceChildren(icon(name))
    target.dataset.flIcon = name
  }


  // Первый экран остаётся текстовым.
  // Демо доступны ниже, в своей галерее.
  document.querySelector('.hero-visual')?.remove()

  const description = document.querySelector(
    '.hero-description',
  )

  if (description) {
    description.textContent =
      'Fluffy - социальная сеть с открытым исходным кодом. ' +
      'Личные сообщения, групповые чаты и профили ' +
      'пользователей - все в одном пространстве. ' +
      'Проект развивается открыто: его можно изучать, ' +
      'тестировать и прокачивать вместе.'
  }

  // Убираем каталог очевидных путей внутри репозитория.
  const resources = document.querySelector(
    '#resources .container',
  )

  if (resources) {
    const heading = node('div', 'section-heading')

    heading.append(
      node('span', 'section-kicker', 'Открытый проект'),
      node('h2', '', 'Изучайте. Пробуйте. Развивайте.'),
      node(
        'p',
        '',
        'Исходный код и обсуждение развития Fluffy доступны ' +
          'на GitHub. Можно разобраться в устройстве проекта ' +
          'или предложить своё улучшение.',
      ),
    )

    const grid = node('div', 'resource-grid')

    const cards = [
      {
        title: 'Исходный код',
        description:
          'Посмотрите, как устроен Fluffy, и запустите ' +
          'свою копию проекта.',
        label: 'Открыть репозиторий',
        href: 'https://github.com/ghostfaccee/Fluffy',
        icon: 'code',
      },
      {
        title: 'Идеи и ошибки',
        description:
          'Нашли проблему или придумали новую возможность? ' +
          'Создайте обращение в репозитории.',
        label: 'Перейти к обращениям',
        href: 'https://github.com/ghostfaccee/Fluffy/issues',
        icon: 'chat',
      },
    ]

    for (const item of cards) {
      const card = node('a', 'resource-card')
      card.href = item.href
      card.target = '_blank'
      card.rel = 'noopener noreferrer'

      const top = node('div', 'resource-card-top')
      const leading = node('span', 'resource-icon')
      const trailing = node('span', 'resource-arrow')

      leading.append(icon(item.icon))
      trailing.append(icon('arrow'))
      top.append(leading, trailing)

      card.append(
        top,
        node('h3', '', item.title),
        node('p', '', item.description),
        node('span', 'resource-link', item.label),
      )

      grid.append(card)
    }

    resources.replaceChildren(heading, grid)
  }

  // Почтовые адреса и их назначение сохраняются.
  document.querySelectorAll('.contact-arrow').forEach(
    (target) => replaceIcon(target, 'arrow'),
  )

  const featureIcons = [
    'chat',
    'users',
    'user',
    'shield',
    'layers',
    'code',
  ]

  document.querySelectorAll('.feature-icon').forEach(
    (target, index) => {
      replaceIcon(
        target,
        featureIcons[index % featureIcons.length],
      )
    },
  )

  document.querySelectorAll(
    '.note-icon, .development-note-icon',
  ).forEach((target) => replaceIcon(target, 'code'))

  document.querySelectorAll('.requirement-check').forEach(
    (target) => replaceIcon(target, 'check'),
  )

  const factIcons = ['code', 'server', 'layers']

  document.querySelectorAll('.fact-value').forEach(
    (target, index) => {
      if (target.querySelector('.fl-icon')) return

      target.prepend(
        icon(factIcons[index % factIcons.length]),
      )
    },
  )

  // Заменяем стрелки в кнопках и текстовых ссылках.
  document.querySelectorAll(
    '.button span[aria-hidden="true"]',
  ).forEach((target) => replaceIcon(target, 'arrow'))

  document.querySelectorAll('.text-link').forEach((target) => {
    const walker = document.createTreeWalker(
      target,
      NodeFilter.SHOW_TEXT,
    )

    while (walker.nextNode()) {
      walker.currentNode.textContent =
        walker.currentNode.textContent.replace(/[↗→]/g, '')
    }

    if (!target.querySelector('.fl-icon')) {
      target.append(icon('arrow'))
    }
  })

  // Старый site.js меняет содержимое переключателей.
  // Следим за ним и возвращаем SVG вместо символов.
  const themeButton = document.querySelector(
    '.header-tools .icon-button:not(.menu-toggle)',
  )

  if (themeButton) {
    const refreshThemeIcon = () => {
      replaceIcon(
        themeButton,
        root.dataset.theme === 'light' ? 'moon' : 'sun',
      )

      document.querySelector(
        'meta[name="theme-color"]',
      )?.setAttribute(
        'content',
        root.dataset.theme === 'light'
          ? '#f4f7f9'
          : '#191a1b',
      )
    }

    refreshThemeIcon()

    new MutationObserver(refreshThemeIcon).observe(
      themeButton,
      { childList: true },
    )
  }

  const menuButton = document.querySelector('.menu-toggle')

  if (menuButton) {
    const refreshMenuIcon = () => {
      replaceIcon(
        menuButton,
        menuButton.getAttribute('aria-expanded') === 'true'
          ? 'close'
          : 'menu',
      )
    }

    refreshMenuIcon()

    new MutationObserver(refreshMenuIcon).observe(
      menuButton,
      {
        childList: true,
        attributes: true,
        attributeFilter: ['aria-expanded'],
      },
    )
  }

  // Галерея пересоздаётся при фильтрации:
  // новые кнопки увеличения тоже получают иконки.
  const gallery = document.querySelector('#demo .demo-grid')

  if (gallery) {
    const refreshGalleryIcons = () => {
      gallery.querySelectorAll('.demo-zoom').forEach(
        (target) => replaceIcon(target, 'zoom'),
      )
    }

    refreshGalleryIcons()

    new MutationObserver(refreshGalleryIcons).observe(
      gallery,
      { childList: true, subtree: true },
    )
  }

  replaceIcon(
    document.querySelector('.lightbox-head .icon-button'),
    'close',
  )

    const viewerButtons = document.querySelectorAll(
    '.lightbox-controls .icon-button',
  )

  replaceIcon(viewerButtons[0], 'left')
  replaceIcon(viewerButtons[1], 'right')
})()
