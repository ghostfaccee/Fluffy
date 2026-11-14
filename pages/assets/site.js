(() => {
  'use strict'

  /*
   * ДЕМО-СКРИНШОТЫ
   *
   * src — путь относительно pages/index.html;
   * title — название;
   * description — подпись;
   * category — код категории из CATEGORIES.
   *
   * Для добавления картинки:
   * 1. Положи её в pages/assets/.
   * 2. Добавь объект в DEMOS.
   *
   * Первый скриншот также показывается на первом экране.
   */

  const CATEGORIES = [
    { id: 'all', label: 'Все экраны' },
    { id: 'intro', label: 'Знакомство' },
    { id: 'chat', label: 'Общение' },
    { id: 'profile', label: 'Профили' },
    { id: 'theme', label: 'Оформление' },
    { id: 'posts', label: 'Посты' },
    { id: 'customization', label: 'Кастомизация' }
  ]

  const DEMOS = [
    {
      src: 'assets/demo/MainPage.png',
      title: 'Первое знакомство',
      description: 'Главная страница для новых пользователей.',
      category: 'intro',
    },
    {
      src: 'assets/demo/Register.png',
      title: 'Регистрация',
      description: 'Создание аккаунта.',
      category: 'intro',
    },
    {
      src: 'assets/demo/Login.png',
      title: 'Авторизация',
      description: 'Вход в аккаунт.',
      category: 'intro',
    },
    {
      src: 'assets/demo/MainPageAfterLogin.png',
      title: 'Теперь ты с нами',
      description: 'Главная страница после регистрации и авторизации.',
      category: 'intro',
    },
    {
      src: 'assets/demo/Chat.png',
      title: 'Личные сообщения',
      description: 'Переписка между пользователями.',
      category: 'chat',
    },
    {
      src: 'assets/demo/GroupChat.png',
      title: 'Групповые чаты',
      description: 'Разговоры с несколькими участниками.',
      category: 'chat',
    },
    {
      src: 'assets/demo/Profile.png',
      title: 'Мой профиль',
      description: 'Личная страница пользователя.',
      category: 'profile',
    },
    {
      src: 'assets/demo/FriendProfile.png',
      title: 'Профили пользователей',
      description: 'Знакомство с другими людьми.',
      category: 'profile',
    },
    {
      src: 'assets/demo/DarkTheme.png',
      title: 'Темная тема',
      description: 'Графитовый фон и спокойные акценты.',
      category: 'theme',
    },
    {
      src: 'assets/demo/LightTheme.png',
      title: 'Светлая тема',
      description: 'Альтернативное оформление приложения.',
      category: 'theme',
    },
    {
      src: 'assets/demo/WritePost.png',
      title: 'Создание поста',
      description: 'Посты имеют заголовок и контент.',
      category: 'posts'
    },
    {
      src: 'assets/demo/Post.png',
      title: 'Посты',
      description: 'Отображение в профиле.',
      category: 'posts'
    },
    {
      src: 'assets/demo/GraphiteAccent.png',
      title: 'Графитовый акцент',
      description: 'Для фанатов строгости и минимализма.',
      category: 'customization'
    },
    {
      src: 'assets/demo/CoffeeAccent.png',
      title: 'Кофейный акцент',
      description: 'Студентам посвящается:',
      category: 'customization'
    },
    {
      src: 'assets/demo/WineAccent.png',
      title: 'Винный акцент',
      description: 'Зато вайбово.',
      category: 'customization'
    },
    {
      src: 'assets/demo/UltramarineAccent.png',
      title: 'Ультрамариновый акцент',
      description: 'Морская глубина.',
      category: 'customization'
    }
  ]

  const root = document.documentElement
  const reduceMotion = window.matchMedia(
    '(prefers-reduced-motion: reduce)',
  )

  root.classList.add('js')

  function element(tag, className, text) {
    const node = document.createElement(tag)

    if (className) node.className = className
    if (text !== undefined) node.textContent = text

    return node
  }

  function button(className, text, label) {
    const node = element('button', className, text)

    node.type = 'button'

    if (label) {
      node.setAttribute('aria-label', label)
    }

    return node
  }

  function setupHeader() {
    const header = document.querySelector('.header-inner')
    const nav = document.querySelector('.nav')

    if (!header) return

    const tools = element('div', 'header-tools')

    const themeButton = button(
      'icon-button',
      '',
      'Переключить тему',
    )

    function applyTheme(theme) {
      root.dataset.theme = theme

      const dark = theme === 'dark'

      themeButton.textContent = dark ? '☀' : '☾'
      themeButton.setAttribute(
        'aria-label',
        dark ? 'Включить светлую тему' : 'Включить тёмную тему',
      )

      document
        .querySelector('meta[name="theme-color"]')
        ?.setAttribute(
          'content',
          dark ? '#171819' : '#f6f7f3',
        )
    }

    let savedTheme = null

    try {
      savedTheme = localStorage.getItem('fluffy.presentation.theme')
    } catch {}

    applyTheme(savedTheme === 'light' ? 'light' : 'dark')

    themeButton.addEventListener('click', () => {
      const next = root.dataset.theme === 'dark'
        ? 'light'
        : 'dark'

      applyTheme(next)

      try {
        localStorage.setItem('fluffy.presentation.theme', next)
      } catch {}
    })

    tools.append(themeButton)

    if (nav) {
      nav.id ||= 'presentation-navigation'

      const menuButton = button(
        'icon-button menu-toggle',
        '☰',
        'Открыть меню',
      )

      menuButton.setAttribute('aria-controls', nav.id)
      menuButton.setAttribute('aria-expanded', 'false')

      function closeMenu() {
        nav.classList.remove('is-open')
        menuButton.setAttribute('aria-expanded', 'false')
        menuButton.setAttribute('aria-label', 'Открыть меню')
        menuButton.textContent = '☰'
      }

      menuButton.addEventListener('click', () => {
        const open = nav.classList.toggle('is-open')

        menuButton.setAttribute('aria-expanded', String(open))
        menuButton.setAttribute(
          'aria-label',
          open ? 'Закрыть меню' : 'Открыть меню',
        )
        menuButton.textContent = open ? '×' : '☰'
      })

      nav.addEventListener('click', (event) => {
        if (event.target.closest('a')) closeMenu()
      })

      document.addEventListener('click', (event) => {
        if (!header.contains(event.target)) closeMenu()
      })

      document.addEventListener('keydown', (event) => {
        if (
          event.key === 'Escape' &&
          nav.classList.contains('is-open')
        ) {
          closeMenu()
          menuButton.focus()
        }
      })

      tools.append(menuButton)
    }

    header.append(tools)
  }

  function setupGallery() {
    const section = document.querySelector('#demo .container')

    if (!section || !DEMOS.length) return

    const heading = section.querySelector('.section-heading')
    const disclaimer = section.querySelector('.demo-disclaimer')

    if (!heading) return

    const toolbar = element('div', 'demo-toolbar')
    const filters = element('div', 'demo-filters')
    const count = element('span', 'demo-count')
    const grid = element('div', 'demo-grid')

    filters.setAttribute('role', 'group')
    filters.setAttribute('aria-label', 'Категории скриншотов')
    count.setAttribute('role', 'status')
    count.setAttribute('aria-live', 'polite')

    let visibleDemos = [...DEMOS]
    let viewerDemos = [...DEMOS]
    let currentIndex = 0
    let opener = null

    // Нативный dialog обеспечивает модальность
    // и удержание фокуса внутри окна.
    const dialog = element('dialog', 'lightbox')

    dialog.setAttribute('aria-labelledby', 'demo-viewer-title')
    dialog.setAttribute(
      'aria-describedby',
      'demo-viewer-description',
    )

    const dialogHead = element('div', 'lightbox-head')
    const dialogTitle = element('h2', 'lightbox-title')
    const closeButton = button(
      'icon-button',
      '×',
      'Закрыть просмотр',
    )

    dialogTitle.id = 'demo-viewer-title'
    closeButton.autofocus = true

    dialogHead.append(dialogTitle, closeButton)

    const image = element('img', 'lightbox-image')
    image.decoding = 'async'

    const dialogFooter = element('div', 'lightbox-footer')
    const description = element('p', 'lightbox-description')
    const controls = element('div', 'lightbox-controls')
    const position = element('span', 'lightbox-position')
    const previous = button(
      'icon-button',
      '←',
      'Предыдущий скриншот',
    )
    const next = button(
      'icon-button',
      '→',
      'Следующий скриншот',
    )

    description.id = 'demo-viewer-description'
    position.setAttribute('aria-live', 'polite')

    controls.append(previous, position, next)
    dialogFooter.append(description, controls)
    dialog.append(dialogHead, image, dialogFooter)
    document.body.append(dialog)

    function renderViewer() {
      const demo = viewerDemos[currentIndex]

      if (!demo) return

      image.src = demo.src
      image.alt = demo.title

      dialogTitle.textContent = demo.title
      description.textContent = demo.description
      position.textContent =
        `${currentIndex + 1} / ${viewerDemos.length}`

      previous.disabled = viewerDemos.length < 2
      next.disabled = viewerDemos.length < 2
    }

    function openViewer(demo, source, list = visibleDemos) {
      if (typeof dialog.showModal !== 'function') {
        // Запасной вариант для старого браузера.
        window.open(demo.src, '_blank', 'noopener,noreferrer')
        return
      }

      viewerDemos = [...list]
      currentIndex = Math.max(0, viewerDemos.indexOf(demo))
      opener = source

      renderViewer()

      dialog.showModal()
      document.body.classList.add('modal-open')
    }

    function moveViewer(direction) {
      if (!viewerDemos.length) return

      currentIndex = (
        currentIndex + direction + viewerDemos.length
      ) % viewerDemos.length

      renderViewer()
    }

    closeButton.addEventListener('click', () => dialog.close())
    previous.addEventListener('click', () => moveViewer(-1))
    next.addEventListener('click', () => moveViewer(1))

    dialog.addEventListener('keydown', (event) => {
      if (event.key === 'ArrowLeft') {
        event.preventDefault()
        moveViewer(-1)
      }

      if (event.key === 'ArrowRight') {
        event.preventDefault()
        moveViewer(1)
      }
    })

    dialog.addEventListener('click', (event) => {
      if (event.target !== dialog) return

      const bounds = dialog.getBoundingClientRect()

      if (
        event.clientX < bounds.left ||
        event.clientX > bounds.right ||
        event.clientY < bounds.top ||
        event.clientY > bounds.bottom
      ) {
        dialog.close()
      }
    })

    dialog.addEventListener('close', () => {
      document.body.classList.remove('modal-open')

      if (opener?.isConnected) {
        opener.focus({ preventScroll: true })
      }

      image.removeAttribute('src')
    })

    function createCard(demo) {
      const figure = element('figure', 'demo-card')
      const open = button(
        'demo-open',
        undefined,
        `Увеличить: ${demo.title}`,
      )

      const preview = element('img')

      preview.src = demo.src
      preview.alt = demo.title
      preview.loading = 'lazy'
      preview.decoding = 'async'

      const zoom = element('span', 'demo-zoom', '↗')
      zoom.setAttribute('aria-hidden', 'true')

      preview.addEventListener('error', () => {
        preview.classList.add('image-failed')
        preview.alt = `Не удалось загрузить: ${demo.title}`
      })

      open.append(preview, zoom)

      open.addEventListener('click', () => {
        openViewer(demo, open)
      })

      const caption = element('figcaption')

      caption.append(
        element('strong', '', demo.title),
        element('span', '', demo.description),
      )

      figure.append(open, caption)

      return figure
    }

    function renderGallery(category) {
      visibleDemos = category === 'all'
        ? [...DEMOS]
        : DEMOS.filter((demo) => demo.category === category)

      grid.replaceChildren(...visibleDemos.map(createCard))
      count.textContent = `Экранов: ${visibleDemos.length}`

      for (const filter of filters.querySelectorAll('button')) {
        filter.setAttribute(
          'aria-pressed',
          String(filter.dataset.category === category),
        )
      }
    }

    for (const category of CATEGORIES) {
      if (
        category.id !== 'all' &&
        !DEMOS.some((demo) => demo.category === category.id)
      ) {
        continue
      }

      const filter = button('filter-button', category.label)
      filter.dataset.category = category.id
      filter.setAttribute('aria-pressed', 'false')

      filter.addEventListener('click', () => {
        renderGallery(category.id)
      })

      filters.append(filter)
    }

    toolbar.append(filters, count)

    // Старые вручную написанные карточки заменяются
    // галереей из массива DEMOS.
    section.replaceChildren(heading, toolbar, grid)

    if (disclaimer) {
      section.append(disclaimer)
    }

    renderGallery('all')

    // На первом экране — настоящий интерфейс,
    // а не декоративная карточка с повторным описанием.
    const visual = document.querySelector(
      '.hero-visual .visual-title',
    )

    if (visual) {
      const featured = DEMOS[0]
      const previewButton = button(
        'hero-preview',
        undefined,
        `Посмотреть интерфейс: ${featured.title}`,
      )

      const preview = element('img')

      preview.src = featured.src
      preview.alt = featured.title
      preview.decoding = 'async'
      preview.fetchPriority = 'high'

      previewButton.append(preview)

      previewButton.addEventListener('click', () => {
        openViewer(featured, previewButton, DEMOS)
      })

      visual.replaceWith(previewButton)
    }
  }

  function setupCopyButtons() {
    for (const pre of document.querySelectorAll('pre')) {
      const code = pre.querySelector('code')

      if (!code) continue

      const copy = button(
        'copy-button',
        'Копировать',
        'Скопировать команду',
      )

      copy.setAttribute('aria-live', 'polite')

      let resetTimer

      copy.addEventListener('click', async () => {
        const text = code.textContent || ''

        clearTimeout(resetTimer)

        try {
          if (!navigator.clipboard?.writeText) {
            throw new Error('Clipboard unavailable')
          }

          await navigator.clipboard.writeText(text)
          copy.textContent = 'Скопировано'
        } catch {
          // На file:// или HTTP доступ к буферу может быть
          // недоступен. Выделяем команду для Ctrl+C.
          const selection = window.getSelection()
          const range = document.createRange()

          range.selectNodeContents(code)
          selection?.removeAllRanges()
          selection?.addRange(range)

          copy.textContent = 'Нажмите Ctrl+C'
        }

        resetTimer = setTimeout(() => {
          copy.textContent = 'Копировать'
        }, 2500)
      })

      pre.append(copy)
    }
  }

  function setupReveal() {
    if (
      reduceMotion.matches ||
      !('IntersectionObserver' in window)
    ) {
      return
    }

    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue

          entry.target.classList.add('is-visible')
          observer.unobserve(entry.target)
        }
      },
      { threshold: 0.08 },
    )

    document.querySelectorAll(
      '.section-heading, .feature-card, .about-note, .step-card',
    ).forEach((node) => {
      node.classList.add('reveal-pending')
      observer.observe(node)
    })
  }

  function setupActiveNavigation() {
    if (!('IntersectionObserver' in window)) return

    const links = [
      ...document.querySelectorAll('.nav a[href^="#"]'),
    ]

    const sections = links
      .map((link) => document.getElementById(
        link.getAttribute('href').slice(1),
      ))
      .filter(Boolean)

    const observer = new IntersectionObserver(
      (entries) => {
        const active = entries
          .filter((entry) => entry.isIntersecting)
          .sort(
            (first, second) =>
              first.boundingClientRect.top -
              second.boundingClientRect.top,
          )[0]

        if (!active) return

        for (const link of links) {
          if (
            link.getAttribute('href') ===
            `#${active.target.id}`
          ) {
            link.setAttribute('aria-current', 'location')
          } else {
            link.removeAttribute('aria-current')
          }
        }
      },
      {
        rootMargin: '-15% 0px -55% 0px',
        threshold: 0,
      },
    )

    sections.forEach((section) => observer.observe(section))
  }

  setupHeader()
  setupGallery()
  setupCopyButtons()
  setupReveal()
  setupActiveNavigation()
})()
