import { onMounted, onBeforeUnmount } from 'vue'
import { useWsStore } from '@/stores/ws'
import { useChatStore } from '@/modules/chat/stores/chat'
import { useGroupStore } from '@/modules/groups/stores/group'

export function useMessagingRealtime() {
  const ws = useWsStore()
  const chat = useChatStore()
  const groups = useGroupStore()

  let unsubscribeMessage = null
  let unsubscribeGroup = null

  function subscribe() {
    // Повторный вызов не должен создавать лишние обработчики.
    unsubscribe()

    unsubscribeMessage = ws.on('new_message', (payload) => {
      chat.handleIncoming(payload)
    })

    unsubscribeGroup = ws.on('new_group_message', (payload) => {
      groups.handleIncoming(payload)
    })
  }

  function unsubscribe() {
    unsubscribeMessage?.()
    unsubscribeGroup?.()

    unsubscribeMessage = null
    unsubscribeGroup = null
  }

  onMounted(() => {
    subscribe()
    ws.connect()
  })

  onBeforeUnmount(() => {
    unsubscribe()

    // Соединение принадлежит приложению, а не отдельной странице.
    // При переходах между страницами его не закрываем.
  })
}
