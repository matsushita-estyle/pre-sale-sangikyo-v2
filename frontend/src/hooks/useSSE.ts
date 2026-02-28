import { useEffect, useState, useCallback } from 'react'
import { agentApi } from '@/lib/api/agent'
import { StreamEvent } from '@/types/agent'

interface UseSSEResult {
  messages: StreamEvent[]
  isStreaming: boolean
  error: string | null
  clearMessages: () => void
}

export const useSSE = (
  userId: string,
  query: string | null
): UseSSEResult => {
  const [messages, setMessages] = useState<StreamEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  useEffect(() => {
    if (!query) return

    setIsStreaming(true)
    setError(null)
    setMessages([])

    const eventSource = agentApi.queryStream(userId, query)

    eventSource.onmessage = (event) => {
      try {
        const data: StreamEvent = JSON.parse(event.data)
        setMessages((prev) => [...prev, data])

        if (data.type === 'done' || data.type === 'error') {
          eventSource.close()
          setIsStreaming(false)
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err)
      }
    }

    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      setError('接続エラーが発生しました')
      eventSource.close()
      setIsStreaming(false)
    }

    return () => {
      eventSource.close()
      setIsStreaming(false)
    }
  }, [userId, query])

  return { messages, isStreaming, error, clearMessages }
}
