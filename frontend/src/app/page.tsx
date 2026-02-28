'use client'

import { useState } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatMessages } from '@/components/chat/ChatMessages'
import { sendChatMessage } from '@/lib/api'
import { useUserStore } from '@/store/userStore'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

function ChatPage() {
  const selectedUserId = useUserStore((state) => state.selectedUserId)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (query: string) => {
    // ユーザーメッセージを追加
    setMessages((prev) => [...prev, { role: 'user', content: query }])
    setIsLoading(true)
    setError(null)

    try {
      // バックエンドAPIを呼び出し（選択されたユーザーIDを使用）
      const response = await sendChatMessage(selectedUserId, query)

      // アシスタントの応答を追加
      setMessages((prev) => [...prev, { role: 'assistant', content: response }])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'エラーが発生しました')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-screen">
      {/* ヘッダー（将来的に情報を追加する可能性あり） */}
      <header className="bg-white border-b border-gray-200 px-6 py-2">
        {/* 将来的にタイトルや情報を追加 */}
      </header>

      {/* メインコンテンツ */}
      <ChatMessages messages={messages} isLoading={isLoading} error={error} />

      {/* 入力フォーム */}
      <div className="px-6 py-4">
        <div className="max-w-4xl mx-auto">
          <ChatInput onSubmit={handleSubmit} disabled={isLoading} />
        </div>
      </div>
    </div>
  )
}

export default function Home() {
  return (
    <MainLayout>
      <ChatPage />
    </MainLayout>
  )
}
