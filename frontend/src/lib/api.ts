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
