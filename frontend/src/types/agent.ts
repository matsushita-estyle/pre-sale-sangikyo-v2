export interface QueryRequest {
  user_id: string
  query: string
}

export interface QueryResponse {
  request_id: string
  user_id: string
  query: string
  response: string
  created_at: string
}

export interface StreamEvent {
  type: 'progress' | 'result' | 'error' | 'done'
  message: string
  data?: unknown
}
