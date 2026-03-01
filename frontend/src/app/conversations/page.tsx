'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { MainLayout } from '@/components/layout/MainLayout'
import { ConversationRow } from '@/components/conversation/ConversationRow'
import { useUserStore } from '@/store/userStore'
import { useConversationStore } from '@/store/conversationStore'
import { MessageSquare } from 'lucide-react'

export default function ConversationsPage() {
  const router = useRouter()
  const selectedUserId = useUserStore((state) => state.selectedUserId)
  const { conversations, isLoading, error, fetchConversations, deleteConversation } =
    useConversationStore()

  useEffect(() => {
    if (selectedUserId) {
      fetchConversations(selectedUserId)
    }
  }, [selectedUserId, fetchConversations])

  const handleSelectConversation = (conversationId: string) => {
    router.push(`/?conversation=${conversationId}`)
  }

  const handleDeleteConversation = async (conversationId: string) => {
    await deleteConversation(conversationId)
  }

  return (
    <MainLayout>
      <div className="h-screen overflow-y-auto">
        {/* Header */}
        <header className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center gap-3">
              <MessageSquare className="w-6 h-6 text-blue-600" />
              <h1 className="text-2xl font-bold text-gray-900">会話履歴</h1>
            </div>
            <p className="text-sm text-gray-600 mt-1">過去の会話を一覧で確認できます</p>
          </div>
        </header>

        {/* Content */}
        <main className="px-6 py-6">
          <div className="max-w-4xl mx-auto">
            {isLoading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                <p className="text-gray-600 mt-4">読み込み中...</p>
              </div>
            )}

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                エラー: {error}
              </div>
            )}

            {!isLoading && !error && conversations.length === 0 && (
              <div className="text-center py-12">
                <MessageSquare className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-600">会話履歴がありません</p>
                <p className="text-sm text-gray-500 mt-2">
                  チャットで質問を開始すると、ここに履歴が表示されます
                </p>
              </div>
            )}

            {!isLoading && !error && conversations.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
                {conversations.map((conversation) => (
                  <ConversationRow
                    key={conversation.id}
                    conversation={conversation}
                    onSelect={handleSelectConversation}
                    onDelete={handleDeleteConversation}
                  />
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </MainLayout>
  )
}
