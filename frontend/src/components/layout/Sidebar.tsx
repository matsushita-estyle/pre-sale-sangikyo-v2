'use client'

import {
  MessageSquare,
  Database,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { UserSelector } from './UserSelector'
import { ConversationList } from '@/components/conversation/ConversationList'

interface SidebarProps {
  isExpanded: boolean
  onToggle: () => void
  onNewConversation?: () => void
  onSelectConversation?: (conversationId: string) => void
}

export function Sidebar({ isExpanded, onToggle, onNewConversation, onSelectConversation }: SidebarProps) {
  const pathname = usePathname()

  const menuItems = [
    { href: '/', icon: MessageSquare, label: 'チャット' },
    { href: '/data', icon: Database, label: 'データ管理' },
  ]

  return (
    <div
      className={`h-screen bg-white border-r border-gray-200 transition-all duration-300 ease-in-out flex-shrink-0 sticky top-0 flex flex-col ${
        isExpanded ? 'w-64' : 'w-16'
      }`}
    >
      {/* ヘッダー */}
      <div className="p-4 flex items-center justify-between border-b border-gray-200 flex-shrink-0">
        <h2
          className={`text-lg font-bold text-gray-900 whitespace-nowrap transition-all duration-300 ${
            isExpanded
              ? 'opacity-100 w-auto'
              : 'opacity-0 w-0 overflow-hidden'
          }`}
        >
          SFA Agent
        </h2>
        <button
          onClick={onToggle}
          className="p-1.5 hover:bg-gray-100 rounded transition-colors flex-shrink-0"
          aria-label={isExpanded ? 'サイドバーを閉じる' : 'サイドバーを開く'}
        >
          {isExpanded ? (
            <ChevronLeft className="w-5 h-5 text-gray-600" />
          ) : (
            <ChevronRight className="w-5 h-5 text-gray-600" />
          )}
        </button>
      </div>

      {/* ナビゲーション */}
      <nav className="p-3 flex-shrink-0">
        <div className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href

            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center px-3 py-2.5 rounded-lg transition-colors group ${
                  isExpanded ? 'gap-3' : 'justify-center'
                } ${
                  isActive
                    ? 'bg-blue-50 text-blue-600'
                    : 'text-gray-700 hover:bg-gray-50'
                }`}
                title={!isExpanded ? item.label : ''}
              >
                <Icon
                  className={`w-5 h-5 flex-shrink-0 ${
                    isActive
                      ? 'text-blue-600'
                      : 'text-gray-500 group-hover:text-gray-700'
                  }`}
                />
                <span
                  className={`text-sm font-medium whitespace-nowrap transition-all duration-300 ${
                    isExpanded
                      ? 'opacity-100 w-auto'
                      : 'opacity-0 w-0 overflow-hidden'
                  }`}
                >
                  {item.label}
                </span>
              </Link>
            )
          })}
        </div>
      </nav>

      {/* 会話履歴リスト */}
      <div className="flex-1 min-h-0">
        <ConversationList
          isExpanded={isExpanded}
          onNewConversation={onNewConversation || (() => {})}
          onSelectConversation={onSelectConversation || (() => {})}
        />
      </div>

      {/* ユーザー選択 */}
      <div className="flex-shrink-0">
        <UserSelector isExpanded={isExpanded} />
      </div>
    </div>
  )
}
