'use client'

import { ReactNode, useState } from 'react'
import { Sidebar } from './Sidebar'

interface MainLayoutProps {
  children: ReactNode
  onNewConversation?: () => void
  onSelectConversation?: (conversationId: string) => void
}

export function MainLayout({ children, onNewConversation, onSelectConversation }: MainLayoutProps) {
  const [isSidebarExpanded, setIsSidebarExpanded] = useState(true)

  return (
    <div className="min-h-screen bg-gray-50 flex" suppressHydrationWarning>
      {/* サイドバー */}
      <Sidebar
        isExpanded={isSidebarExpanded}
        onToggle={() => setIsSidebarExpanded(!isSidebarExpanded)}
        onNewConversation={onNewConversation}
        onSelectConversation={onSelectConversation}
      />

      {/* メインコンテンツエリア */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* メインコンテンツ */}
        <main className="flex-1">{children}</main>
      </div>
    </div>
  )
}
