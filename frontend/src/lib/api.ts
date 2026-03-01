/**
 * API client for backend communication
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface User {
  user_id: string
  name: string
  email: string
  department?: string
  role?: string
}

export interface Customer {
  customer_id: string
  name: string
  industry?: string
  contact_person?: string
  email?: string
  phone?: string
}

export interface Deal {
  deal_id: string
  customer_id: string
  customer_name?: string
  sales_user_id: string
  sales_user_name?: string
  deal_stage: string
  deal_amount?: number
  service_type?: string
  last_contact_date?: string
  notes?: string
}

export async function getUsers(): Promise<User[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/users`)
  if (!response.ok) {
    throw new Error('Failed to fetch users')
  }
  return response.json()
}

export async function getCustomers(): Promise<Customer[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/customers`)
  if (!response.ok) {
    throw new Error('Failed to fetch customers')
  }
  return response.json()
}

export async function getDeals(): Promise<Deal[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/deals`)
  if (!response.ok) {
    throw new Error('Failed to fetch deals')
  }
  return response.json()
}

export interface ChatRequest {
  user_id: string
  query: string
}

export interface ChatResponse {
  response: string
}

export async function sendChatMessage(
  userId: string,
  query: string
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/api/v1/copilot/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      query: query,
    }),
  })

  if (!response.ok) {
    throw new Error('Failed to send chat message')
  }

  const data: ChatResponse = await response.json()
  return data.response
}

// Conversation API types
export interface Message {
  message_id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  search_history?: any[]
}

export interface Conversation {
  id: string
  user_id: string
  title: string
  messages: Message[]
  created_at: string
  updated_at: string
  is_active: boolean
}

export async function getUserConversations(userId: string): Promise<Conversation[]> {
  const response = await fetch(`${API_BASE_URL}/api/v1/users/${userId}/conversations`)
  if (!response.ok) {
    throw new Error('Failed to fetch conversations')
  }
  return response.json()
}

export async function getConversation(conversationId: string): Promise<Conversation> {
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}`)
  if (!response.ok) {
    throw new Error('Failed to fetch conversation')
  }
  return response.json()
}

export async function deleteConversation(conversationId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/conversations/${conversationId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error('Failed to delete conversation')
  }
}
