'use client'

import { useState } from 'react'
import { Header } from '@/components/layout/Header'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatMessage } from '@/components/chat/ChatMessage'
import { ProgressIndicator } from '@/components/chat/ProgressIndicator'
import { useSSE } from '@/hooks/useSSE'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentQuery, setCurrentQuery] = useState<string | null>(null)

  const { messages: sseEvents, isStreaming, error } = useSSE('1', currentQuery)

  const handleSubmit = (query: string) => {
    // ユーザーメッセージを追加
    setMessages((prev) => [...prev, { role: 'user', content: query }])
    // SSE ストリーミング開始
    setCurrentQuery(query)
  }

  // SSE が完了したら結果をメッセージに追加
  if (!isStreaming && sseEvents.length > 0 && currentQuery) {
    const resultEvent = sseEvents.find((e) => e.type === 'result')
    if (resultEvent) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: resultEvent.message },
      ])
      setCurrentQuery(null)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-4xl">
        <div className="space-y-4">
          {/* メッセージ履歴 */}
          {messages.map((message, idx) => (
            <ChatMessage
              key={idx}
              role={message.role}
              content={message.content}
            />
          ))}

          {/* 進捗インジケーター */}
          {currentQuery && (
            <ProgressIndicator events={sseEvents} isStreaming={isStreaming} />
          )}

          {/* エラー表示 */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}
        </div>
      </main>

      {/* 入力フォーム */}
      <div className="sticky bottom-0 bg-white border-t border-gray-200 shadow-lg">
        <div className="container mx-auto px-4 py-4 max-w-4xl">
          <ChatInput onSubmit={handleSubmit} disabled={isStreaming} />
        </div>
      </div>
    </div>
  )
}
