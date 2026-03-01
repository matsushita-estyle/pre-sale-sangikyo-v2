'use client'

import { useState } from 'react'
import { MessageSquare, Trash2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'
import { Conversation } from '@/lib/api'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'

interface ConversationCardProps {
  conversation: Conversation
  onSelect: (conversationId: string) => void
  onDelete: (conversationId: string) => Promise<void>
}

export function ConversationCard({ conversation, onSelect, onDelete }: ConversationCardProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const getTitle = () => {
    if (conversation.title && conversation.title !== '新規会話') {
      return conversation.title
    }
    const firstUserMessage = conversation.messages.find((m) => m.role === 'user')
    if (firstUserMessage) {
      return (
        firstUserMessage.content.slice(0, 60) +
        (firstUserMessage.content.length > 60 ? '...' : '')
      )
    }
    return '新規会話'
  }

  const getMessageCount = () => {
    return conversation.messages.length
  }

  const getRelativeTime = () => {
    return formatDistanceToNow(new Date(conversation.updated_at), {
      addSuffix: true,
      locale: ja,
    })
  }

  const handleDelete = async () => {
    try {
      await onDelete(conversation.id)
      setShowDeleteDialog(false)
    } catch (error) {
      console.error('Failed to delete conversation:', error)
    }
  }

  return (
    <>
      <div className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
        {/* Header */}
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-start gap-3 flex-1 min-w-0">
            <div className="p-2 bg-blue-50 rounded-lg flex-shrink-0">
              <MessageSquare className="w-5 h-5 text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <h3
                className="text-sm font-semibold text-gray-900 mb-1 cursor-pointer hover:text-blue-600 truncate"
                onClick={() => onSelect(conversation.id)}
              >
                {getTitle()}
              </h3>
              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span>{getMessageCount()}件のメッセージ</span>
                <span>•</span>
                <span>{getRelativeTime()}</span>
              </div>
            </div>
          </div>
          <button
            onClick={() => setShowDeleteDialog(true)}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0"
            title="削除"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>

        {/* Preview */}
        {conversation.messages.length > 0 && (
          <div className="text-xs text-gray-600 line-clamp-2 bg-gray-50 p-2 rounded border border-gray-100">
            {conversation.messages[conversation.messages.length - 1].content}
          </div>
        )}
      </div>

      {/* Delete confirmation dialog */}
      {showDeleteDialog && (
        <DeleteConfirmDialog
          conversationTitle={getTitle()}
          onConfirm={handleDelete}
          onCancel={() => setShowDeleteDialog(false)}
        />
      )}
    </>
  )
}
