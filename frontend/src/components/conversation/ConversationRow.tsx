'use client'

import { useState } from 'react'
import { MessageSquare, Trash2 } from 'lucide-react'
import { Conversation } from '@/lib/api'
import { DeleteConfirmDialog } from './DeleteConfirmDialog'
import { formatRelativeTime } from '@/lib/dateUtils'

interface ConversationRowProps {
  conversation: Conversation
  onSelect: (conversationId: string) => void
  onDelete: (conversationId: string) => Promise<void>
}

export function ConversationRow({ conversation, onSelect, onDelete }: ConversationRowProps) {
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  const getTitle = () => {
    if (conversation.title && conversation.title !== '新規会話') {
      return conversation.title
    }
    const firstUserMessage = conversation.messages.find((m) => m.role === 'user')
    if (firstUserMessage) {
      return (
        firstUserMessage.content.slice(0, 80) +
        (firstUserMessage.content.length > 80 ? '...' : '')
      )
    }
    return '新規会話'
  }

  const getMessageCount = () => {
    return conversation.messages.length
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
      <div className="bg-white border-b border-gray-200 hover:bg-gray-50 transition-colors">
        <div className="flex items-center gap-4 px-6 py-4">
          {/* Icon */}
          <div className="p-2 bg-blue-50 rounded-lg flex-shrink-0">
            <MessageSquare className="w-5 h-5 text-blue-600" />
          </div>

          {/* Content */}
          <div
            className="flex-1 min-w-0 cursor-pointer"
            onClick={() => onSelect(conversation.id)}
          >
            <h3 className="text-sm font-semibold text-gray-900 mb-1 truncate hover:text-blue-600">
              {getTitle()}
            </h3>
            <div className="flex items-center gap-4 text-xs text-gray-500">
              <span>{getMessageCount()}件のメッセージ</span>
              <span>•</span>
              <span>{formatRelativeTime(conversation.updated_at)}</span>
            </div>
          </div>

          {/* Delete button */}
          <button
            onClick={() => setShowDeleteDialog(true)}
            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0"
            title="削除"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
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
