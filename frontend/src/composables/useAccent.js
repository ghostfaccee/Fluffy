import { readonly, ref } from 'vue'

const accents = Object.freeze([
  { id: 'green', name: 'Мятный', color: '#42C99A' },
  { id: 'graphite', name: 'Графитовый', color: '#858591' },
  { id: 'earth', name: 'Кофейный', color: '#AD7957' },
  { id: 'wine', name: 'Винный', color: '#C4506A' },
  { id: 'blue', name: 'Ультрамарин', color: '#3B46F2' },
])

const selected = ref('green')
let initialized = false

function apply(id) {
  const accent = accents.find((item) => item.id === id) || accents[0]
  const root = document.documentElement
  const hex = accent.color.slice(1)

  const channels = [0, 2, 4].map((offset) =>
    parseInt(hex.slice(offset, offset + 2), 16),
  )

  const linear = channels.map((channel) => {
    const value = channel / 255

    return value <= 0.04045
      ? value / 12.92
      : ((value + 0.055) / 1.055) ** 2.4
  })

  const luminance =
    linear[0] * 0.2126 +
    linear[1] * 0.7152 +
    linear[2] * 0.0722

  const light = channels.map((channel) =>
    Math.round(channel + (255 - channel) * 0.25),
  )

  selected.value = accent.id

  root.style.setProperty('--accent', accent.color)
  root.style.setProperty(
    '--on-accent',
    luminance > 0.179 ? '#111318' : '#FFFFFF',
  )

  // Совместимость с существующими компонентами.
  root.style.setProperty('--green', accent.color)
  root.style.setProperty('--green-light', `rgb(${light.join(', ')})`)
  root.style.setProperty('--fluffy-accent', accent.color)
  root.style.setProperty(
    '--fluffy-on-accent',
    luminance > 0.179 ? '#111318' : '#FFFFFF',
  )

  root.dataset.accent = accent.id
}

function initAccent() {
  if (initialized) return
  initialized = true

  let saved = 'green'

  try {
    saved = localStorage.getItem('fluffy-accent') || 'green'
  } catch {
    // Если хранилище недоступно, используем стандартный цвет.
  }

  apply(saved)

  window.addEventListener('storage', (event) => {
    if (event.key === 'fluffy-accent') {
      apply(event.newValue || 'green')
    } else if (event.key === null) {
      apply('green')
    }
  })
}

function setAccent(id) {
  if (!accents.some((item) => item.id === id)) return

  apply(id)

  try {
    localStorage.setItem('fluffy-accent', id)
  } catch {
    // Выбранный цвет продолжит работать до перезагрузки.
  }
}

export function useAccent() {
  initAccent()

  return {
    accents,
    selectedAccent: readonly(selected),
    setAccent,
  }
}
