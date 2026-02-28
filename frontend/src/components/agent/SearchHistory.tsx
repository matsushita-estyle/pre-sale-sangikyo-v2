'use client'

import { useState } from 'react'
import { SearchHistoryItem } from '@/types/agent'

interface SearchHistoryProps {
  items: SearchHistoryItem[]
}

export function SearchHistory({ items }: SearchHistoryProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (items.length === 0) {
    return null
  }

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded text-sm text-gray-600 cursor-pointer transition-colors"
      >
        <span className="flex items-center space-x-2">
          <span className="text-gray-400">{isExpanded ? '▼' : '▶'}</span>
          <span>実行した検索 ({items.length}件)</span>
        </span>
      </button>

      {isExpanded && (
        <div className="mt-2 px-4 py-3 bg-gray-50 border border-gray-200 rounded space-y-3">
          {items.map((item, idx) => (
            <SearchHistoryItemView key={idx} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

interface SearchHistoryItemViewProps {
  item: SearchHistoryItem
}

function SearchHistoryItemView({ item }: SearchHistoryItemViewProps) {
  return (
    <div className="space-y-1">
      <div className="font-medium text-gray-700 text-sm">{item.toolName}</div>
      {Object.keys(item.arguments).length > 0 && (
        <div className="text-xs text-gray-600">
          引数:{' '}
          {Object.entries(item.arguments)
            .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
            .join(', ')}
        </div>
      )}
      <div className="text-xs text-gray-700">{item.result}</div>
    </div>
  )
}
