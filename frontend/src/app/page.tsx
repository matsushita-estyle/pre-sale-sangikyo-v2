'use client'

import { useState, useEffect } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatMessages } from '@/components/chat/ChatMessages'
import { useUserStore } from '@/store/userStore'
import { useAgentStream } from '@/hooks/useAgentStream'
import { SearchHistoryItem } from '@/types/agent'

interface Message {
  role: 'user' | 'assistant'
  content: string
  searchHistory?: SearchHistoryItem[]
}

function ChatPage() {
  const selectedUserId = useUserStore((state) => state.selectedUserId)
  const [messages, setMessages] = useState<Message[]>([])

  // エージェントストリームフック
  const {
    events: agentEvents,
    currentMessage: agentCurrentMessage,
    finalResponse,
    searchHistory,
    isLoading,
    error,
    sendQuery,
  } = useAgentStream()

  const handleSubmit = async (query: string) => {
    // ユーザーメッセージを追加
    setMessages((prev) => [...prev, { role: 'user', content: query }])

    // エージェントクエリを送信（SSEストリーム）
    await sendQuery(selectedUserId, query)
  }

  // 最終レスポンスが来たらメッセージに追加（検索履歴も含める）
  useEffect(() => {
    if (finalResponse) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: finalResponse,
          searchHistory: searchHistory,
        },
      ])
    }
  }, [finalResponse, searchHistory])

  return (
    <div className="flex flex-col h-screen">
      {/* ヘッダー（将来的に情報を追加する可能性あり） */}
      <header className="bg-white border-b border-gray-200 px-6 py-2">
        {/* 将来的にタイトルや情報を追加 */}
      </header>

      {/* メインコンテンツ */}
      <ChatMessages
        messages={messages}
        isLoading={isLoading}
        error={error}
        agentEvents={agentEvents}
        agentCurrentMessage={agentCurrentMessage}
      />

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
