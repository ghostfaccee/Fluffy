<script setup>
const year = new Date().getFullYear()
</script>

<template>
  <footer class="footer footer--app" id="footer">
    <div class="container">
      <div class="footer-main">
        <div class="footer-brand">
          <div class="footer-title">Fluffy</div>
          <p>Тихое место в шумной сети. Общение, свобода и открытая разработка.</p>
        </div>
        <div class="footer-links">
          <div class="footer-column">
            <h4>Документация</h4>
            <RouterLink to="/docs/api">Документация API</RouterLink>
            <RouterLink to="/docs/features">Возможности</RouterLink>
            <RouterLink to="/docs/principles">Принципы</RouterLink>
          </div>
          <div class="footer-column">
            <h4>О проекте</h4>
            <RouterLink to="/docs/manifesto">Манифест</RouterLink>
            <RouterLink to="/docs/opensource">Open Source</RouterLink>
            <RouterLink to="/docs/credits">Титры</RouterLink>
          </div>
          <div class="footer-column">
            <h4>Сообщество</h4>
            <a href="https://github.com/ghostfaccee/Fluffy" target="_blank" rel="noopener noreferrer">GitHub</a>
            <a href="mailto:fluffy.social.network@gmail.com">Связаться</a>
            <RouterLink to="/login">Войти</RouterLink>
            <RouterLink to="/register">Регистрация</RouterLink>
          </div>
        </div>
      </div>
      <div class="footer-bottom">
        <span>{{ year }} Fluffy Project.</span>
        <span>Made with love by ghostfaccee.</span>
      </div>
    </div>
  </footer>
</template>
