'use client'

import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatMessage } from '@/components/chat/ChatMessage'
import { sendChatMessage } from '@/lib/api'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (query: string) => {
    // ユーザーメッセージを追加
    setMessages((prev) => [...prev, { role: 'user', content: query }])
    setIsLoading(true)
    setError(null)

    try {
      // バックエンドAPIを呼び出し
      const response = await sendChatMessage('1', query)

      // アシスタントの応答を追加
      setMessages((prev) => [...prev, { role: 'assistant', content: response }])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <MainLayout>
      <div className="flex flex-col h-screen">
        {/* ヘッダー（将来的に情報を追加する可能性あり） */}
        <header className="bg-white border-b border-gray-200 px-6 py-2">
          {/* 将来的にタイトルや情報を追加 */}
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

            {/* ローディング表示 */}
            {isLoading && (
              <div className="flex items-center space-x-2 text-gray-600">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
                <span>回答を生成中...</span>
              </div>
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
        <div className="px-6 py-4">
          <div className="max-w-4xl mx-auto">
            <ChatInput onSubmit={handleSubmit} disabled={isLoading} />
          </div>
        </div>
      </div>
    </MainLayout>
  )
}
