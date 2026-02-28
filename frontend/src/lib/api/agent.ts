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
  queryStream: (userId: string, query: string): EventSource => {
    const url = new URL(`${API_URL}/api/v1/sales-agent/query-stream`)
    url.searchParams.set('user_id', userId)
    url.searchParams.set('query', query)

    return new EventSource(url.toString())
  },

  /**
   * ヘルスチェック
   */
  health: async (): Promise<{ status: string; initialized: boolean }> => {
    const res = await fetch(`${API_URL}/api/v1/health`)
    return res.json()
  },
}
