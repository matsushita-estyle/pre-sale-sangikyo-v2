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

// エージェント進捗イベントの型定義
export type ProgressEventType =
  | 'thinking'
  | 'function_call'
  | 'function_result'
  | 'response_chunk'
  | 'final_response'
  | 'error'

export interface ProgressEvent {
  type: ProgressEventType
  message?: string
  tool_name?: string
  arguments?: Record<string, any>
  result?: string
  content?: string
  conversation_id?: string
}

export interface AgentQueryRequest {
  user_id: string
  query: string
}

export interface AgentQueryResponse {
  response: string
}

// 検索履歴アイテム
export interface SearchHistoryItem {
  toolName: string
  arguments: Record<string, any>
  result: string
}
