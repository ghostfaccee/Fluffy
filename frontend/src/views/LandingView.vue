<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import LogoIcon from '@/components/LogoIcon.vue'

const year = new Date().getFullYear()

const menuOpen = ref(false)
const openDropdown = ref(null)

function toggleDropdown(name) {
  openDropdown.value = openDropdown.value === name ? null : name
}

function closeMenus() {
  openDropdown.value = null
  menuOpen.value = false
}

function onDocumentClick(event) {
  if (!event.target.closest('.nav-dropdown')) openDropdown.value = null
}

function onKeydown(event) {
  if (event.key === 'Escape') closeMenus()
}

let observer

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)

  observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
          observer.unobserve(entry.target)
        }
      })
    },
    { threshold: 0.12 },
  )
  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el))
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
  observer?.disconnect()
})
</script>

<template>
    <header class="header">
        <div class="container nav">
            <RouterLink to="/" class="logo" aria-label="Fluffy - Главная">
                <LogoIcon />
                <span class="logo-name">Fluffy</span>
            </RouterLink>
            <nav class="nav-links" :class="{ open: menuOpen }" aria-label="Базовая навигация">
                <div class="nav-dropdown" :class="{ open: openDropdown === 'features' }">
                    <button class="nav-dropdown-toggle" type="button"
                        :aria-expanded="openDropdown === 'features'"
                        @click="toggleDropdown('features')">
                        Возможности <span class="dropdown-chevron" aria-hidden="true">⌄</span>
                    </button>
                    <div class="dropdown-menu">
                        <a href="#features" @click="closeMenus">Все возможности</a>
                        <a href="#manifest" @click="closeMenus">Как устроена Fluffy</a>
                        <a href="#principles" @click="closeMenus">Наши принципы</a>
                    </div>
                </div>
                <div class="nav-dropdown" :class="{ open: openDropdown === 'opensource' }">
                    <button class="nav-dropdown-toggle" type="button"
                        :aria-expanded="openDropdown === 'opensource'"
                        @click="toggleDropdown('opensource')">
                        Открытый код <span class="dropdown-chevron" aria-hidden="true">⌄</span>
                    </button>
                    <div class="dropdown-menu">
                        <a href="#opensource" @click="closeMenus">Об исходном коде</a>
                        <a href="#contribute" @click="closeMenus">Как помочь проекту</a>
                        <a href="https://github.com/" target="_blank" rel="noopener noreferrer" @click="closeMenus">GitHub</a>
                    </div>
                </div>
                <div class="nav-dropdown" :class="{ open: openDropdown === 'about' }">
                    <button class="nav-dropdown-toggle" type="button"
                        :aria-expanded="openDropdown === 'about'"
                        @click="toggleDropdown('about')">
                        О нас <span class="dropdown-chevron" aria-hidden="true">⌄</span>
                    </button>
                    <div class="dropdown-menu">
                        <a href="#manifest" @click="closeMenus">Философия Fluffy</a>
                        <a href="#principles" @click="closeMenus">Наши ценности</a>
                        <a href="#principles" @click="closeMenus">О команде и проекте</a>
                    </div>
                </div>
                <div class="nav-dropdown" :class="{ open: openDropdown === 'project' }">
                    <button class="nav-dropdown-toggle" type="button"
                        :aria-expanded="openDropdown === 'project'"
                        @click="toggleDropdown('project')">
                        О проекте <span class="dropdown-chevron" aria-hidden="true">⌄</span>
                    </button>
                    <div class="dropdown-menu">
                        <a href="#principles" @click="closeMenus">Что такое Fluffy</a>
                        <a href="#opensource" @click="closeMenus">Технологии</a>
                        <a href="#footer" @click="closeMenus">Контакты</a>
                    </div>
                </div>
            </nav>
            <div class="nav-actions">
                <RouterLink to="/login" class="btn btn-secondary">Войти</RouterLink>
                <RouterLink to="/register" class="btn btn-primary">Регистрация</RouterLink>
                <button class="menu-toggle" type="button"
                    :aria-expanded="menuOpen"
                    :aria-label="menuOpen ? 'Закрыть меню' : 'Открыть меню'"
                    @click="menuOpen = !menuOpen">{{ menuOpen ? '×' : '☰' }}</button>
            </div>
        </div>
    </header>
    <main>
        <section class="hero" id="home">
            <div class="container hero-content">
                <h1>
                    Тихое место<br>
                    <span class="gradient-text">в шумной сети.</span>
                </h1>
                <p class="hero-description">
                    Fluffy - не очередной проект. 
                    Это пространство для общения без лишнего шума.
                    Делись моментами, находи своих людей и сам решай,
                    что заслуживает твоего внимания.
                </p>
            </div>
        </section>
        <div class="announcement">
            Fluffy - независимый open-source проект.
            <a href="#opensource">Узнать больше ↗</a>
        </div>
        <section class="section" id="features">
            <div class="container">
                <div class="section-heading reveal">
                    <h2>Всё нужное.<br>Ничего лишнего.</h2>
                    <p>
                        Социальная сеть должна помогать общаться,
                        а не отвлекать от жизни.
                    </p>
                </div>
                <div class="features-grid">
                    <article class="feature-card reveal">
                        <div class="feature-mark"></div>
                        <h3>Ничего лишнего</h3>
                        <p>
                            Никаких рекомендаций, трендов и «тебе может понравиться». 
                            Лента строится только из того, на что ты подписался сам.
                        </p>
                    </article>
                    <article class="feature-card reveal">
                        <div class="feature-mark"></div>
                        <h3>Живое общение</h3>
                        <p>
                            Находи единомышленников, обсуждай идеи
                            и поддерживай связь с людьми без
                            лишних сложностей.
                        </p>
                    </article>
                    <article class="feature-card reveal">
                        <div class="feature-mark"></div>
                        <h3>Тишина по умолчанию</h3>
                        <p>
                            Никаких реклам или подписок, спама или рассылок.
                            Только то, что необходимо.
                        </p>
                    </article>
                    <article class="feature-card reveal">
                        <div class="feature-mark"></div>
                        <h3>Меньше лишнего</h3>
                        <p>
                            Только понятный интерфейс, спокойные цвета
                            и внимание к главному.
                        </p>
                    </article>
                    <article class="feature-card reveal">
                        <div class="feature-mark"></div>
                        <h3>Сообщество</h3>
                        <p>
                            Знакомься с новыми людьми, участвуй
                            в обсуждениях и помогай формировать
                            культуру самого проекта.
                        </p>
                    </article>
                    <article class="feature-card reveal">
                        <div class="feature-mark"></div>
                        <h3>Открытый исходный код</h3>
                        <p>
                            Изучай реализацию, предлагай изменения
                            и при желании участвуй в развитии
                            проекта вместе с сообществом.
                        </p>
                    </article>
                </div>
            </div>
        </section>
        <section class="section manifest" id="manifest">
            <div class="container manifest-grid">
                <div class="manifest-content reveal">
                    <h2>
                        Интернет должен быть
                        <span class="gradient-text">уютным.</span>
                    </h2>
                    <p>
                        Современный человек привык к бесконечной ленте, скроллингу
                        и быстрому дофамину. Наш проект задуман иначе.
                    </p>
                    <p>
                        Fluffy - место, где важны не цифры на экране, а
                        сообщество. Где можно предлагать свои решения и
                        развивать проект вместе.
                    </p>
                    <div class="manifest-list">
                        <div class="manifest-item">
                            <span class="check">✓</span>
                            <div>
                                <strong>Все в твоих руках</strong>
                                <p>Ты можешь внедрять свои фичи и реализовывать свои идеи</p>
                            </div>
                        </div>
                        <div class="manifest-item">
                            <span class="check">✓</span>
                            <div>
                                <strong>Свобода выбора</strong>
                                <p>Ты сам определяешь что будешь видеть в ленте</p>
                            </div>
                        </div>
                        <div class="manifest-item">
                            <span class="check">✓</span>
                            <div>
                                <strong>Минимализм</strong>
                                <p>Только самое необходимое</p>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="quote-card reveal">
                    <div class="quote-mark">“</div>
                    <blockquote>
                        Социальные сети должны давать энергию,
                        а не пожирать её.
                    </blockquote>
                    <small>Ghostfaccee - Автор и основатель проекта</small>
                </div>
            </div>
        </section>
        <section class="section" id="principles">
            <div class="container">
                <div class="section-heading reveal">
                    <h2>Создаём по-другому.</h2>
                    <p>
                        Идеала не существует. Но лучше стремиться к нему,
                        чем стоять на месте.
                    </p>
                </div>
                <div class="values-grid">
                    <article class="value-card reveal">
                        <div class="value-number">01</div>
                        <h3>Простота</h3>
                        <p>Понятный интерфейс без визуального шума.</p>
                    </article>
                    <article class="value-card reveal">
                        <div class="value-number">02</div>
                        <h3>Открытость</h3>
                        <p>Публичный исходный код проекта.</p>
                    </article>
                    <article class="value-card reveal">
                        <div class="value-number">03</div>
                        <h3>Сообщество</h3>
                        <p>Развитие вместе с участниками проекта.</p>
                    </article>
                    <article class="value-card reveal">
                        <div class="value-number">04</div>
                        <h3>Осознанность</h3>
                        <p>Технологии должны служить людям, а не наоборот.</p>
                    </article>
                </div>
            </div>
        </section>
        <section class="section opensource" id="opensource">
            <div class="container opensource-grid">
                <div class="opensource-content reveal" id="contribute">
                    <h2>
                        Не просто продукт.<br>
                        <span class="gradient-text">Общее дело.</span>
                    </h2>
                    <p>
                        Fluffy - открытый проект, который развивается
                        вместе с сообществом. Изучай код, сообщай об 
                        ошибках, предлагай идеи и помогай создавать новые возможности.
                    </p>
                    <p>
                        Мы хотим, чтобы каждый мог понять, как устроен
                        проект, и при желании внести свой вклад.
                    </p>
                    <div class="tech-list">
                        <span class="tech-tag">FastAPI</span>
                        <span class="tech-tag">Vue</span>
                        <span class="tech-tag">Open source</span>
                    </div>
                    <div class="opensource-link">
                        <a
                            href="https://github.com/ghostfaccee/Fluffy"
                            target="_blank"
                            rel="noopener noreferrer"
                            class="btn btn-primary"
                        >
                            GitHub
                        </a>
                    </div>
                </div>
                <div class="repository-card reveal">
                    <div class="repo-header">
                        <div class="repo-mark"></div>
                        <div>
                            <h3>Fluffy</h3>
                            <p>Независимый open-source проект</p>
                        </div>
                        <span class="repo-badge">PUBLIC</span>
                    </div>
                    <div class="repo-details">
                        <div class="repo-row">
                            <span>Frontend</span>
                            <span>Vue 3 + Vite</span>
                        </div>
                        <div class="repo-row">
                            <span>Backend</span>
                            <span>FastAPI</span>
                        </div>
                        <div class="repo-row">
                            <span>Язык backend</span>
                            <span>Python</span>
                        </div>
                        <div class="repo-row">
                            <span>Лицензия</span>
                            <span>Будет определена</span>
                        </div>
                        <div class="repo-row">
                            <span>Статус</span>
                            <span style="color: var(--green-light);">
                                В разработке
                            </span>
                        </div>
                    </div>
                </div>
            </div>
        </section>
    </main>
    <footer class="footer" id="footer">
        <div class="container">
            <div class="footer-main">
                <div class="footer-brand">
                    <div class="footer-title">Fluffy</div>
                    <p>
                        Тихое место в шумной сети.
                        Общение, свобода и открытая разработка.
                    </p>
                </div>
                <div class="footer-links">
                    <div class="footer-column">
                        <h4>Проект</h4>
                        <a href="#principles">О Fluffy</a>
                        <a href="#manifest">Наши принципы</a>
                        <a href="#features">Возможности</a>
                    </div>
                    <div class="footer-column">
                        <h4>Сообщество</h4>
                        <a href="#opensource">Open Source</a>
                        <a
                            href="https://github.com/ghostfaccee/Fluffy"
                            target="_blank"
                            rel="noopener noreferrer"
                        >GitHub</a>
                        <a href="mailto:fluffy.social.network@gmail.com">Связаться</a>
                    </div>
                    <div class="footer-column">
                        <h4>Аккаунт</h4>
                        <RouterLink to="/login">Войти</RouterLink>
                        <RouterLink to="register">Регистрация</RouterLink>
                    </div>
                </div>
            </div>
            <div class="footer-bottom">
                <span>
                    {{ year }} Fluffy Project.
                </span>
                <span>Made with love by ghostfaccee.</span>
            </div>
        </div>
    </footer>
</template>
