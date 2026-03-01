'use client'

import { useState, useEffect, useCallback } from 'react'
import { MainLayout } from '@/components/layout/MainLayout'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatMessages } from '@/components/chat/ChatMessages'
import { useUserStore } from '@/store/userStore'
import { useConversationStore } from '@/store/conversationStore'
import { useAgentStream } from '@/hooks/useAgentStream'
import { getConversation } from '@/lib/api'
import { SearchHistoryItem } from '@/types/agent'

interface Message {
  role: 'user' | 'assistant'
  content: string
  searchHistory?: SearchHistoryItem[]
}

export default function Home() {
  const selectedUserId = useUserStore((state) => state.selectedUserId)
  const { fetchConversations, startNewConversation } = useConversationStore()
  const [messages, setMessages] = useState<Message[]>([])

  // エージェントストリームフック
  const {
    events: agentEvents,
    currentMessage: agentCurrentMessage,
    finalResponse,
    searchHistory,
    isLoading,
    error,
    conversationId,
    sendQuery,
  } = useAgentStream()

  const handleSubmit = async (query: string) => {
    // ユーザーメッセージを追加
    setMessages((prev) => [...prev, { role: 'user', content: query }])

    // エージェントクエリを送信（SSEストリーム） - conversationIdを渡す
    await sendQuery(selectedUserId, query, conversationId || undefined)
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
      // 会話履歴を再取得
      if (selectedUserId) {
        fetchConversations(selectedUserId)
      }
    }
  }, [finalResponse, searchHistory, selectedUserId, fetchConversations])

  // 新規会話を開始
  const handleNewConversation = useCallback(() => {
    setMessages([])
    startNewConversation()
  }, [startNewConversation])

  // 会話を選択して復元
  const handleSelectConversation = useCallback(async (convId: string) => {
    try {
      const conversation = await getConversation(convId)
      // メッセージを復元
      const restoredMessages: Message[] = conversation.messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        searchHistory: msg.search_history || undefined,
      }))
      setMessages(restoredMessages)
    } catch (error) {
      console.error('Failed to load conversation:', error)
    }
  }, [])

  return (
    <MainLayout
      onNewConversation={handleNewConversation}
      onSelectConversation={handleSelectConversation}
    >
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
    </MainLayout>
  )
}
