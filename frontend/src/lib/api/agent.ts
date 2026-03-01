import { QueryRequest, QueryResponse } from '@/types/agent'

const API_URL =
  process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const agentApi = {
  /**
   * エージェントに問い合わせ（通常）
   */
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    const res = await fetch(`${API_URL}/api/v1/sales-agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })

    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`)
    }

    return res.json()
  },

  /**
   * エージェントに問い合わせ（SSE ストリーミング）
   */
  queryStream: async (
    userId: string,
    query: string,
    onEvent: (event: any) => void,
    onError?: (error: Error) => void
  ): Promise<void> => {
    const res = await fetch(`${API_URL}/api/v1/agent/query-stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, query }),
    })

    if (!res.ok) {
      throw new Error(`API Error: ${res.status} ${res.statusText}`)
    }

    const reader = res.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error('Response body is null')
    }

    try {
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6)
            try {
              const event = JSON.parse(data)
              onEvent(event)
            } catch (e) {
              console.error('Failed to parse SSE data:', data)
            }
          }
        }
      }
    } catch (error) {
      if (onError) {
        onError(error as Error)
      } else {
        throw error
      }
    }
  },

  /**
   * ヘルスチェック
   */
  health: async (): Promise<{ status: string; initialized: boolean }> => {
    const res = await fetch(`${API_URL}/api/v1/health`)
    return res.json()
  },
}
