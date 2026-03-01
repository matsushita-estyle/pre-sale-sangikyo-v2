'use client'

import { create } from 'zustand'
import { Conversation, getUserConversations, deleteConversation as apiDeleteConversation } from '@/lib/api'

interface ConversationStore {
  conversations: Conversation[]
  selectedConversationId: string | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchConversations: (userId: string) => Promise<void>
  selectConversation: (conversationId: string | null) => void
  startNewConversation: () => void
  deleteConversation: (conversationId: string) => Promise<void>
}

export const useConversationStore = create<ConversationStore>((set) => ({
  conversations: [],
  selectedConversationId: null,
  isLoading: false,
  error: null,

  fetchConversations: async (userId: string) => {
    set({ isLoading: true, error: null })
    try {
      const conversations = await getUserConversations(userId)
      set({ conversations, isLoading: false })
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch conversations',
        isLoading: false,
      })
    }
  },

  selectConversation: (conversationId: string | null) => {
    set({ selectedConversationId: conversationId })
  },

  startNewConversation: () => {
    set({ selectedConversationId: null })
  },

  deleteConversation: async (conversationId: string) => {
    set({ isLoading: true, error: null })
    try {
      await apiDeleteConversation(conversationId)
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== conversationId),
        selectedConversationId:
          state.selectedConversationId === conversationId ? null : state.selectedConversationId,
        isLoading: false,
      }))
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to delete conversation',
        isLoading: false,
      })
      throw error
    }
  },
}))
