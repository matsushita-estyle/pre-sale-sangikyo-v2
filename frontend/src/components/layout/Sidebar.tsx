'use client'

import {
  MessageSquare,
  Database,
  ChevronRight,
  ChevronLeft,
} from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

interface SidebarProps {
  isExpanded: boolean
  onToggle: () => void
}

export function Sidebar({ isExpanded, onToggle }: SidebarProps) {
  const pathname = usePathname()

  const menuItems = [
    { href: '/', icon: MessageSquare, label: 'チャット' },
    { href: '/data', icon: Database, label: 'データ管理' },
  ]

  return (
    <div
      className={`h-screen bg-white border-r border-gray-200 transition-all duration-300 ease-in-out flex-shrink-0 sticky top-0 ${
        isExpanded ? 'w-64' : 'w-16'
      }`}
    >
      <div className="flex flex-col h-full">
        {/* ヘッダー */}
        <div className="p-4 flex items-center justify-between border-b border-gray-200">
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
        <nav className="flex-1 p-3 overflow-y-auto">
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

        {/* フッター */}
        <div className="p-3 border-t border-gray-200">
          <div
            className={`px-3 py-2 text-xs text-gray-500 ${
              isExpanded ? 'block' : 'hidden'
            }`}
          >
            <p className="font-semibold mb-1">SFA Agent V2</p>
            <p>Powered by ESTYLE</p>
          </div>
        </div>
      </div>
    </div>
  )
}
