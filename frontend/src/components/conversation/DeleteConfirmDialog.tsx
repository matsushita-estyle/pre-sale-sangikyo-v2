'use client'

import { useState } from 'react'
import { AlertTriangle } from 'lucide-react'

interface DeleteConfirmDialogProps {
  conversationTitle: string
  onConfirm: () => void
  onCancel: () => void
}

export function DeleteConfirmDialog({
  conversationTitle,
  onConfirm,
  onCancel,
}: DeleteConfirmDialogProps) {
  const [isDeleting, setIsDeleting] = useState(false)

  const handleConfirm = async () => {
    setIsDeleting(true)
    try {
      await onConfirm()
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2 bg-red-100 rounded-full">
            <AlertTriangle className="w-6 h-6 text-red-600" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900">会話を削除</h2>
        </div>

        {/* Message */}
        <p className="text-gray-600 mb-2">以下の会話を削除してもよろしいですか？</p>
        <p className="text-sm font-medium text-gray-900 mb-4 p-3 bg-gray-50 rounded border border-gray-200">
          {conversationTitle}
        </p>
        <p className="text-sm text-gray-500 mb-6">この操作は取り消せません。</p>

        {/* Actions */}
        <div className="flex gap-3 justify-end">
          <button
            onClick={onCancel}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            キャンセル
          </button>
          <button
            onClick={handleConfirm}
            disabled={isDeleting}
            className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isDeleting ? '削除中...' : '削除'}
          </button>
        </div>
      </div>
    </div>
  )
}
