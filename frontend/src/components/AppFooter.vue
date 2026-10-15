<script setup>
const year = new Date().getFullYear()
</script>

<template>
  <footer class="footer footer--app" id="footer">
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