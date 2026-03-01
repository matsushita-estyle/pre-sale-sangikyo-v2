'use client'

import { useState, useCallback } from 'react'
import { ProgressEvent, SearchHistoryItem } from '@/types/agent'

interface AgentStreamState {
  events: ProgressEvent[]
  currentMessage: string
  finalResponse: string | null
  searchHistory: SearchHistoryItem[]
  isLoading: boolean
  error: string | null
  conversationId: string | null
}

export function useAgentStream() {
  const [state, setState] = useState<AgentStreamState>({
    events: [],
    currentMessage: '',
    finalResponse: null,
    searchHistory: [],
    isLoading: false,
    error: null,
    conversationId: null,
  })

  const sendQuery = useCallback(async (userId: string, query: string, conversationId?: string) => {
    // 状態リセット (conversationIdは保持)
    setState((prev) => ({
      events: [],
      currentMessage: '',
      finalResponse: null,
      searchHistory: [],
      isLoading: true,
      error: null,
      conversationId: prev.conversationId,
    }))

    // function_callとfunction_resultのペアを保存するための一時マップ
    const functionCallMap = new Map<string, { arguments: Record<string, any> }>()

    try {
      // SSEリクエストを送信
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/api/v1/agent/query-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          query,
          conversation_id: conversationId || null
        }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is null')
      }

      // ストリームを読み取る
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')

        // 最後の不完全な行をバッファに保持
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6).trim()
            if (!data) continue

            try {
              const progressEvent: ProgressEvent = JSON.parse(data)

              // conversation_idを保存
              if (progressEvent.conversation_id) {
                setState((prev) => ({
                  ...prev,
                  conversationId: progressEvent.conversation_id || null,
                }))
              }

              // function_callを記録
              if (progressEvent.type === 'function_call' && progressEvent.tool_name) {
                functionCallMap.set(progressEvent.tool_name, {
                  arguments: progressEvent.arguments || {},
                })
              }

              // function_resultが来たら検索履歴に追加
              if (progressEvent.type === 'function_result' && progressEvent.tool_name) {
                const toolName = progressEvent.tool_name
                const functionCall = functionCallMap.get(toolName)
                if (functionCall) {
                  setState((prev) => ({
                    ...prev,
                    searchHistory: [
                      ...prev.searchHistory,
                      {
                        toolName,
                        arguments: functionCall.arguments,
                        result: progressEvent.result || '',
                      },
                    ],
                  }))
                  functionCallMap.delete(toolName)
                }
              }

              setState((prev) => {
                const newState = {
                  ...prev,
                  events: [...prev.events, progressEvent],
                }

                // イベントタイプに応じて状態を更新
                if (progressEvent.type === 'final_response') {
                  newState.finalResponse = progressEvent.content || null
                  newState.isLoading = false
                  newState.currentMessage = ''
                } else if (progressEvent.type === 'error') {
                  newState.error = progressEvent.message || 'エラーが発生しました'
                  newState.isLoading = false
                  newState.currentMessage = ''
                } else if (progressEvent.message) {
                  newState.currentMessage = progressEvent.message
                }

                return newState
              })
            } catch (e) {
              console.error('Failed to parse SSE data:', e, data)
            }
          }
        }
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'エラーが発生しました',
      }))
    }
  }, [])

  const reset = useCallback(() => {
    setState({
      events: [],
      currentMessage: '',
      finalResponse: null,
      searchHistory: [],
      isLoading: false,
      error: null,
    })
  }, [])

  return { ...state, sendQuery, reset }
}
