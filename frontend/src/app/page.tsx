'use client'

import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
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
    <MainLayout>
      <div className="flex flex-col h-screen">
        {/* ヘッダー */}
        <header className="bg-white border-b border-gray-200 px-6 py-4">
          <h1 className="text-2xl font-bold text-gray-900">
            営業支援AIエージェント
          </h1>
          <p className="text-sm text-gray-600 mt-1">
            質問を入力してください
          </p>
        </header>

        {/* メインコンテンツ */}
        <main className="flex-1 overflow-y-auto px-6 py-8">
          <div className="max-w-4xl mx-auto space-y-4">
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
        <div className="bg-white border-t border-gray-200 px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <ChatInput onSubmit={handleSubmit} disabled={isStreaming} />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
