'use client'

import { User } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { getUsers } from '@/lib/api'
import { useUserStore } from '@/store/userStore'

interface UserSelectorProps {
  isExpanded: boolean
}

export function UserSelector({ isExpanded }: UserSelectorProps) {
  const { selectedUserId, setSelectedUserId } = useUserStore()

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: getUsers,
  })

  const selectedUser = users.find((u) => u.user_id === selectedUserId)

  return (
    <div className="p-3 border-t border-gray-200">
      <div className={`${isExpanded ? 'block' : 'hidden'}`}>
        <label className="text-xs font-semibold text-gray-700 mb-2 block">
          ユーザー選択
        </label>
        <select
          value={selectedUserId}
          onChange={(e) => setSelectedUserId(e.target.value)}
          className="w-full px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        >
          {isLoading ? (
            <option>読み込み中...</option>
          ) : (
            users.map((user) => (
              <option key={user.user_id} value={user.user_id}>
                {user.name}
              </option>
            ))
          )}
        </select>
      </div>
      {!isExpanded && (
        <div className="flex justify-center" title={selectedUser?.name}>
          <User className="w-5 h-5 text-gray-500" />
        </div>
      )}
    </div>
  )
}
