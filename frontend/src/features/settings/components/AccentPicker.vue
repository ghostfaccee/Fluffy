<script setup>
import { useAccent } from '@/composables/useAccent'

const { accents, selectedAccent, setAccent } = useAccent()
</script>

<template>
  <section class="accent-picker">
    <h2>Цвет акцента</h2>
    <p>Кнопки, выделения и активные разделы. Сохраняется на этом устройстве.</p>

    <div class="accent-picker__options" role="group" aria-label="Цвет акцента">
      <button
        v-for="accent in accents"
        :key="accent.id"
        type="button"
        class="accent-choice"
        :class="{ 'is-selected': selectedAccent === accent.id }"
        :aria-pressed="selectedAccent === accent.id"
        @click="setAccent(accent.id)"
      >
        <span
          class="accent-choice__swatch"
          :style="{ backgroundColor: accent.color }"
          aria-hidden="true"
        >
          <span v-if="selectedAccent === accent.id">✓</span>
        </span>
        <span>{{ accent.name }}</span>
      </button>
    </div>
  </section>
</template>

<style scoped>
.accent-picker {
  padding: 20px;
  margin-bottom: 20px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: var(--bg-card);
}

.accent-picker h2 {
  margin: 0;
  color: var(--text);
  font-size: 17px;
  font-weight: 650;
}

.accent-picker p {
  margin: 8px 0 18px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.6;
}

.accent-picker__options {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.accent-choice {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 8px 11px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--bg);
  color: var(--text);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
}

.accent-choice.is-selected {
  border-color: var(--accent);
  box-shadow: 0 0 0 1px var(--accent);
}

.accent-choice__swatch {
  display: grid;
  place-items: center;
  width: 27px;
  height: 27px;
  border: 1px solid rgb(255 255 255 / 15%);
  border-radius: 8px;
}

.accent-choice__swatch span {
  color: var(--on-accent);
  font-weight: 750;
}

.accent-choice:focus-visible {
  outline: 2px solid var(--text);
  outline-offset: 4px;
}
</style>
