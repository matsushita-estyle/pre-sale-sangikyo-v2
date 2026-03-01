'use client'

import { useEffect } from 'react'
import { useConversationStore } from '@/store/conversationStore'
import { useUserStore } from '@/store/userStore'
import { ConversationListItem } from './ConversationListItem'
import { Plus } from 'lucide-react'

interface ConversationListProps {
  isExpanded: boolean
  onNewConversation: () => void
  onSelectConversation: (conversationId: string) => void
}

export function ConversationList({
  isExpanded,
  onNewConversation,
  onSelectConversation,
}: ConversationListProps) {
  const selectedUserId = useUserStore((state) => state.selectedUserId)
  const {
    conversations,
    selectedConversationId,
    isLoading,
    fetchConversations,
    selectConversation,
  } = useConversationStore()

  // ユーザー選択時に会話履歴を取得
  useEffect(() => {
    if (selectedUserId) {
      fetchConversations(selectedUserId)
    }
  }, [selectedUserId, fetchConversations])

  const handleNewConversation = () => {
    selectConversation(null)
    onNewConversation()
  }

  const handleSelectConversation = (conversationId: string) => {
    selectConversation(conversationId)
    onSelectConversation(conversationId)
  }

  return (
    <div className="flex flex-col border-t border-gray-200 h-full">
      {/* 会話履歴ヘッダー */}
      {isExpanded && (
        <div className="px-3 py-2 flex-shrink-0">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider">
            会話履歴
          </h3>
        </div>
      )}

      {/* 新規会話ボタン */}
      <div className="px-3 pb-2 flex-shrink-0">
        <button
          onClick={handleNewConversation}
          className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 transition-colors ${
            isExpanded ? '' : 'justify-center'
          }`}
          title={isExpanded ? '' : '新規会話'}
        >
          <Plus className="w-4 h-4 flex-shrink-0" />
          {isExpanded && <span className="text-sm font-medium">新規会話</span>}
        </button>
      </div>

      {/* 会話リスト */}
      <div className="flex-1 overflow-y-auto px-3 space-y-1 min-h-0 pb-2">
        {isLoading && isExpanded && (
          <p className="text-xs text-gray-500 text-center py-2">読み込み中...</p>
        )}
        {!isLoading && conversations.length === 0 && isExpanded && (
          <p className="text-xs text-gray-500 text-center py-2">
            会話履歴がありません
          </p>
        )}
        {conversations.map((conversation) => (
          <ConversationListItem
            key={conversation.id}
            conversation={conversation}
            isSelected={selectedConversationId === conversation.id}
            onClick={() => handleSelectConversation(conversation.id)}
            isExpanded={isExpanded}
          />
        ))}
      </div>
    </div>
  )
}
