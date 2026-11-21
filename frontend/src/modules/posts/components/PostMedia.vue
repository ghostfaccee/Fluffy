<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { isPostVideo, postsApi } from '../api/posts'

const props = defineProps({
  post: {
    type: Object,
    required: true,
  },
})

const url = ref('')
const failed = ref(false)
const refreshing = ref(false)
const retryError = ref('')
const version = ref(0)
const video = computed(() => isPostVideo(url.value))

let generation = 0

watch(
  [() => props.post.post_id, () => props.post.media_url],
  ([, mediaUrl]) => {
    generation += 1
    url.value = mediaUrl ?? ''
    failed.value = false
    refreshing.value = false
    retryError.value = ''
    version.value += 1
  },
  { immediate: true },
)

async function refresh() {
  if (refreshing.value) return

  const request = ++generation
  const id = props.post.post_id

  refreshing.value = true
  retryError.value = ''

  try {
    const post = await postsApi.get(id)
    if (request !== generation) return

    if (!post.media_url) {
      url.value = ''
      retryError.value = 'У этой публикации больше нет вложения.'
      return
    }

    url.value = post.media_url
    version.value += 1
    failed.value = false
  } catch (cause) {
    if (request !== generation) return

    retryError.value =
      cause?.status === 429
        ? 'Слишком много запросов. Попробуйте немного позже.'
        : 'Не удалось обновить ссылку на вложение.'
  } finally {
    if (request === generation) refreshing.value = false
  }
}

onBeforeUnmount(() => {
  generation += 1
})
</script>

<template>
  <div v-if="url || failed" class="post-media">
    <div v-if="failed" class="post-media__status">
      <p role="status">
        {{
          retryError ||
          'Не удалось открыть вложение. Ссылка могла истечь или браузер не поддерживает этот формат.'
        }}
      </p>

      <button
        v-if="url"
        class="btn btn-secondary btn-small"
        type="button"
        :disabled="refreshing"
        @click="refresh"
      >
        {{ refreshing ? 'Обновляем…' : 'Обновить ссылку' }}
      </button>
    </div>

    <video
      v-else-if="video"
      :key="`video:${version}`"
      class="post-media__asset post-media__asset--video"
      :src="url"
      :aria-label="`Видео к публикации «${post.title}»`"
      controls
      playsinline
      preload="none"
      @error="failed = true"
    />

    <img
      v-else
      :key="`image:${version}`"
      class="post-media__asset post-media__asset--image"
      :src="url"
      :alt="`Изображение к публикации «${post.title}»`"
      loading="lazy"
      decoding="async"
      @error="failed = true"
    />
  </div>
</template>

<style scoped>
.post-media {
  box-sizing: border-box;
  width: min(100%, var(--post-media-width, 560px));
  min-width: 0;
  overflow: hidden;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: color-mix(in srgb, currentColor 4%, transparent);
}

.post-media__asset {
  display: block;
  width: 100%;
  height: auto;
  object-fit: contain;
}

.post-media__asset--image {
  max-height: var(--post-media-image-height, min(360px, 52vh));
}

.post-media__asset--video {
  max-height: var(--post-media-video-height, min(320px, 48vh));
  aspect-ratio: 16 / 9;
  background: #111318;
}

.post-media__status {
  padding: 14px;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.5;
}

.post-media__status p {
  margin: 0 0 8px;
}

@media (max-width: 600px) {
  .post-media__asset--image {
    max-height: var(--post-media-image-height, min(280px, 44vh));
    max-height: var(--post-media-image-height, min(280px, 44svh));
  }

  .post-media__asset--video {
    max-height: var(--post-media-video-height, min(240px, 40vh));
    max-height: var(--post-media-video-height, min(240px, 40svh));
  }
}
</style>
