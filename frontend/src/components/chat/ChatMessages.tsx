'use client'

import { useEffect, useRef } from 'react'
import { ChatMessage } from './ChatMessage'
import { AgentProgress } from '../agent/AgentProgress'
import { AlertCircle } from 'lucide-react'
import { ProgressEvent, SearchHistoryItem } from '@/types/agent'

interface Message {
  role: 'user' | 'assistant'
  content: string
  searchHistory?: SearchHistoryItem[]
}

interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  error: string | null
  agentEvents?: ProgressEvent[]
  agentCurrentMessage?: string
}

export function ChatMessages({
  messages,
  isLoading,
  error,
  agentEvents = [],
  agentCurrentMessage = '',
}: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 新しいメッセージが追加されたら自動スクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, agentEvents])

  return (
    <main className="flex-1 overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        {/* メッセージ履歴 */}
        {messages.map((message, idx) => (
          <ChatMessage
            key={idx}
            role={message.role}
            content={message.content}
            searchHistory={message.searchHistory}
          />
        ))}

        {/* エージェント進捗表示（ローディング中のみ） */}
        {isLoading && (
          <div className="mb-6">
            <AgentProgress events={agentEvents} currentMessage={agentCurrentMessage} />
          </div>
        )}

        {/* エラー表示 */}
        {error && (
          <div className="flex items-start space-x-3 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-4">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">エラーが発生しました</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* 自動スクロール用の要素 */}
        <div ref={messagesEndRef} />
      </div>
    </main>
  )
}
