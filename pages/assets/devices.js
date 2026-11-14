(() => {
  'use strict'

  // Пути относительно pages/index.html.
  const SCREENSHOTS = {
    desktop: 'assets/demo/LaptopView.png',
    mobile: 'assets/demo/MobileView.png',
  }

  const hero = document.querySelector('.hero-inner')

  if (!hero || hero.querySelector('.hero-devices')) return

  function createElement(tag, className, text) {
    const element = document.createElement(tag)

    if (className) {
      element.className = className
    }

    if (text !== undefined) {
      element.textContent = text
    }

    return element
  }

  function createScreen({
    className,
    src,
    alt,
    placeholderTitle,
    placeholderText,
  }) {
    const screen = createElement(
      'div',
      `device-screen ${className}`,
    )

    const placeholder = createElement(
      'div',
      'device-placeholder',
    )

    placeholder.append(
      createElement('strong', '', placeholderTitle),
      createElement('span', '', placeholderText),
    )

    const image = createElement('img')

    image.alt = alt
    image.decoding = 'async'

    // Пока картинка не загрузилась, показываем заглушку.
    image.hidden = true
    image.style.display = 'none'

    image.addEventListener('load', () => {
      image.hidden = false
      image.style.removeProperty('display')
      screen.classList.add('is-loaded')
    })

    image.addEventListener('error', () => {
      image.hidden = true
      image.style.display = 'none'
      screen.classList.remove('is-loaded')
    })

    screen.append(placeholder, image)

    // Назначаем src после обработчиков:
    // загрузка из кеша также будет обработана.
    image.src = src

    return screen
  }

  const composition = createElement(
    'div',
    'hero-devices',
  )

  const laptop = createElement('div', 'device-laptop')
  const laptopLid = createElement('div', 'device-laptop-lid')
  const laptopCamera = createElement(
    'span',
    'device-laptop-camera',
  )
  const laptopBase = createElement(
    'div',
    'device-laptop-base',
  )

  laptopCamera.setAttribute('aria-hidden', 'true')
  laptopBase.setAttribute('aria-hidden', 'true')

  laptopLid.append(
    laptopCamera,
    createScreen({
      className: 'device-laptop-screen',
      src: SCREENSHOTS.desktop,
      alt: 'Интерфейс Fluffy на ноутбуке',
      placeholderTitle: 'Fluffy',
      placeholderText:
        'Здесь будет скриншот десктопной версии',
    }),
  )

  laptop.append(laptopLid, laptopBase)

  const phone = createElement('div', 'device-phone')

  phone.append(
    createScreen({
      className: 'device-phone-screen',
      src: SCREENSHOTS.mobile,
      alt: 'Мобильный интерфейс Fluffy',
      placeholderTitle: 'Fluffy',
      placeholderText: 'Мобильная версия',
    }),
  )

  composition.append(laptop, phone)
  hero.append(composition)
})()
