import { onBeforeUnmount, ref, watch } from 'vue'

const MAX_METADATA_BYTES = 32 * 1024 * 1024

async function readLimitedBlob(response) {
  const contentLength = Number(response.headers.get('content-length'))

  if (
    Number.isFinite(contentLength) &&
    contentLength > MAX_METADATA_BYTES
  ) {
    if (response.body) {
      await response.body.cancel()
    }

    throw new Error('METADATA_FILE_TOO_LARGE')
  }

  // В современных браузерах fetch предоставляет ReadableStream.
  // Без него не скачиваем неизвестный объём данных.
  if (!response.body) {
    throw new Error('METADATA_STREAM_UNAVAILABLE')
  }

  const reader = response.body.getReader()
  const chunks = []
  let totalBytes = 0

  try {
    while (true) {
      const { done, value } = await reader.read()

      if (done) break

      totalBytes += value.byteLength

      if (totalBytes > MAX_METADATA_BYTES) {
        await reader.cancel()
        throw new Error('METADATA_FILE_TOO_LARGE')
      }

      chunks.push(value)
    }
  } finally {
    reader.releaseLock()
  }

  return new Blob(chunks, {
    type: response.headers.get('content-type') || '',
  })
}

function cleanText(value) {
  return typeof value === 'string' ? value.trim() : ''
}

export function useMusicMetadata(getMusicUrl) {
  const title = ref('')
  const artist = ref('')
  const coverUrl = ref('')
  const loading = ref(false)
  const notice = ref('')

  let controller = null
  let generation = 0
  let disposed = false

  function releaseCover() {
    if (coverUrl.value) {
      URL.revokeObjectURL(coverUrl.value)
      coverUrl.value = ''
    }
  }

  async function load(url) {
    const current = ++generation

    controller?.abort()
    controller = null

    releaseCover()

    title.value = ''
    artist.value = ''
    notice.value = ''
    loading.value = false

    if (!url) return

    const requestController = new AbortController()
    controller = requestController
    loading.value = true

    try {
      const response = await fetch(url, {
        method: 'GET',
        mode: 'cors',
        credentials: 'omit',
        signal: requestController.signal,
      })

      if (!response.ok) {
        throw new Error('METADATA_HTTP_ERROR')
      }

      const blob = await readLimitedBlob(response)

      if (disposed || current !== generation) return

      // Загружаем парсер только когда действительно есть аудиофайл.
      const { parseBlob } = await import('music-metadata')

      if (disposed || current !== generation) return

      const metadata = await parseBlob(blob, {
        duration: false,
        skipCovers: false,
      })

      if (disposed || current !== generation) return

      title.value = cleanText(metadata.common.title)

      artist.value =
        cleanText(metadata.common.artist) ||
        (metadata.common.artists || [])
          .map(cleanText)
          .filter(Boolean)
          .join(', ') ||
        cleanText(metadata.common.albumartist)

      const pictures = metadata.common.picture || []

      // Предпочитаем переднюю обложку. SVG намеренно не используем.
      const supportedPictures = pictures.filter((picture) =>
        /^image\/(jpeg|jpg|png|webp|gif)$/i.test(picture.format || ''),
      )

      const picture =
        supportedPictures.find((item) =>
          /front/i.test(item.type || ''),
        ) || supportedPictures[0]

      if (picture?.data?.byteLength) {
        const imageBlob = new Blob([picture.data], {
          type: picture.format,
        })

        coverUrl.value = URL.createObjectURL(imageBlob)
      }
    } catch (cause) {
      if (
        disposed ||
        current !== generation ||
        requestController.signal.aborted
      ) {
        return
      }

      if (cause?.message === 'METADATA_FILE_TOO_LARGE') {
        notice.value =
          'Для файлов больше 32 МиБ теги здесь не считываются.'
      } else {
        notice.value =
          'Теги недоступны. Это не мешает воспроизведению.'
      }
    } finally {
      if (!disposed && current === generation) {
        loading.value = false
        controller = null
      }
    }
  }

  watch(getMusicUrl, load, { immediate: true })

  onBeforeUnmount(() => {
    disposed = true
    generation += 1
    controller?.abort()
    releaseCover()
  })

  return {
    title,
    artist,
    coverUrl,
    loading,
    notice,
  }
}
