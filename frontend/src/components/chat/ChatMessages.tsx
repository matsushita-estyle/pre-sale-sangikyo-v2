'use client'

import { useEffect, useRef } from 'react'
import { ChatMessage } from './ChatMessage'
import { AlertCircle } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  error: string | null
}

export function ChatMessages({ messages, isLoading, error }: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 新しいメッセージが追加されたら自動スクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <main className="flex-1 overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
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
          <div className="flex items-center space-x-2 text-gray-600 mb-4">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
            <span>回答を生成中...</span>
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
