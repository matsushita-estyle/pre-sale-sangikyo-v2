'use client'

import { Conversation } from '@/lib/api'
import { formatRelativeTime } from '@/lib/dateUtils'
import { MessageSquare } from 'lucide-react'

interface ConversationListItemProps {
  conversation: Conversation
  isSelected: boolean
  onClick: () => void
  isExpanded: boolean
}

export function ConversationListItem({
  conversation,
  isSelected,
  onClick,
  isExpanded,
}: ConversationListItemProps) {
  // タイトル生成: 最初のユーザーメッセージから30文字
  const getTitle = () => {
    if (conversation.title && conversation.title !== '新規会話') {
      return conversation.title
    }
    const firstUserMessage = conversation.messages.find((m) => m.role === 'user')
    if (firstUserMessage) {
      return firstUserMessage.content.slice(0, 30) + (firstUserMessage.content.length > 30 ? '...' : '')
    }
    return '新規会話'
  }

  return (
    <button
      onClick={onClick}
      className={`w-full px-3 py-2.5 rounded-lg transition-colors text-left flex items-start gap-3 ${
        isSelected
          ? 'bg-blue-50 text-blue-600'
          : 'text-gray-700 hover:bg-gray-50'
      } ${isExpanded ? '' : 'justify-center'}`}
      title={isExpanded ? '' : getTitle()}
    >
      <MessageSquare
        className={`w-4 h-4 flex-shrink-0 mt-0.5 ${
          isSelected ? 'text-blue-600' : 'text-gray-500'
        }`}
      />
      {isExpanded && (
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">{getTitle()}</p>
          <p className="text-xs text-gray-500 truncate mt-0.5">{formatRelativeTime(conversation.updated_at)}</p>
        </div>
      )}
    </button>
  )
}
