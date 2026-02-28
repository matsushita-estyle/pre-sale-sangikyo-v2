'use client'

import { ChatMessage } from './ChatMessage'

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
  return (
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
  )
}
