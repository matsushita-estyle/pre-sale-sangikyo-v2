import { create } from 'zustand'

interface UserStore {
  selectedUserId: string
  setSelectedUserId: (userId: string) => void
}

export const useUserStore = create<UserStore>((set) => ({
  selectedUserId: '1',
  setSelectedUserId: (userId) => set({ selectedUserId: userId }),
}))
