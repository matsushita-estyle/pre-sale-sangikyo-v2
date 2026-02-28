# エージェント進捗通信の実装プラン

**日付:** 2026-03-01
**概要:** SSEを使ったエージェント進捗通信の段階的実装計画
**参照:** [16_agent_progress_communication.md](16_agent_progress_communication.md)

---

## 実装方針

### アプローチ
1. **モックデータで先に仕組みを作る**（エンドツーエンドで動作確認）
2. **実際のエージェント機能は後で統合**（Function Calling実装後）

### メリット
- UIの動作を先に確認できる
- バックエンド・フロントエンドの連携を早期に検証
- エージェント実装時に進捗送信部分だけ差し替えれば良い

---

## フェーズ1: スキーマ定義とモック実装（2-3時間）

### ステップ1-1: 型定義の作成（30分）

#### タスク1: バックエンドのスキーマ定義
**ファイル:** `backend/app/schemas/agent.py`

```python
"""エージェント関連のスキーマ定義"""

from enum import Enum
from typing import Any
from pydantic import BaseModel


class ProgressEventType(str, Enum):
    """進捗イベントの種類"""

    THINKING = "thinking"  # 思考中
    FUNCTION_CALL = "function_call"  # ツール呼び出し
    FUNCTION_RESULT = "function_result"  # ツール実行結果
    RESPONSE_CHUNK = "response_chunk"  # レスポンス（部分）
    FINAL_RESPONSE = "final_response"  # 最終レスポンス
    ERROR = "error"  # エラー


class ProgressEvent(BaseModel):
    """進捗イベント"""

    type: ProgressEventType
    message: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    result: str | None = None
    content: str | None = None


class AgentQueryRequest(BaseModel):
    """エージェントクエリリクエスト"""

    user_id: str
    query: str


class AgentQueryResponse(BaseModel):
    """エージェントクエリレスポンス（非ストリーミング）"""

    response: str
```

**確認方法:**
```bash
cd backend
python -c "from app.schemas.agent import ProgressEvent, ProgressEventType; print('OK')"
```

---

#### タスク2: フロントエンドの型定義
**ファイル:** `frontend/src/types/agent.ts`

```typescript
/**
 * エージェント進捗イベントの型定義
 */

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
}

export interface AgentQueryRequest {
  user_id: string
  query: string
}

export interface AgentQueryResponse {
  response: string
}
```

**確認方法:**
TypeScriptのコンパイルエラーがないこと

---

### ステップ1-2: バックエンドのモック実装（1時間）

#### タスク3: モックオーケストレーターの作成
**ファイル:** `backend/app/agent/mock_orchestrator.py`

```python
"""モックエージェントオーケストレーター（開発用）"""

import asyncio
from typing import AsyncIterator

from app.schemas.agent import ProgressEvent, ProgressEventType


class MockAgentOrchestrator:
    """モックエージェント（SSEの動作確認用）"""

    async def execute_query_stream(
        self, user_id: str, query: str
    ) -> AsyncIterator[ProgressEvent]:
        """
        モッククエリを実行し、進捗状況をストリームで返す

        Args:
            user_id: ユーザーID
            query: クエリ

        Yields:
            ProgressEvent: 進捗イベント
        """
        # ステップ1: ユーザー情報取得
        yield ProgressEvent(
            type=ProgressEventType.THINKING, message="ユーザー情報を取得中..."
        )
        await asyncio.sleep(1)

        # ステップ2: 顧客検索
        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_CALL,
            tool_name="search_customers",
            arguments={"industries": ["IT", "通信"]},
            message="顧客を検索中...",
        )
        await asyncio.sleep(1.5)

        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_RESULT,
            tool_name="search_customers",
            result="3件の顧客が見つかりました",
        )
        await asyncio.sleep(0.5)

        # ステップ3: ニュース取得
        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_CALL,
            tool_name="search_latest_news",
            arguments={"keywords": ["KDDI", "5G"]},
            message="最新ニュースを取得中...",
        )
        await asyncio.sleep(1.5)

        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_RESULT,
            tool_name="search_latest_news",
            result="5件のニュースが見つかりました",
        )
        await asyncio.sleep(0.5)

        # ステップ4: レポート作成
        yield ProgressEvent(
            type=ProgressEventType.THINKING, message="レポートを作成中..."
        )
        await asyncio.sleep(2)

        # ステップ5: 最終レスポンス
        mock_response = """## 担当案件一覧

---

### KDDI株式会社
- 案件ID: 1
- **ステージ**: 商談
- **サービス種別**: 通信インフラ構築
- **金額**: ¥50,000,000

---

### ソフトバンク株式会社
- 案件ID: 2
- **ステージ**: 提案
- **サービス種別**: 技術人材派遣
- **金額**: ¥30,000,000

---

## 最新ニュース

- KDDI、5G基地局を西日本エリアに拡大
- ソフトバンク、ネットワークエンジニア採用強化
"""

        yield ProgressEvent(type=ProgressEventType.FINAL_RESPONSE, content=mock_response)
```

**確認方法:**
```python
import asyncio
from app.agent.mock_orchestrator import MockAgentOrchestrator

async def test():
    orchestrator = MockAgentOrchestrator()
    async for event in orchestrator.execute_query_stream("1", "テスト"):
        print(f"{event.type}: {event.message or event.content}")

asyncio.run(test())
```

---

#### タスク4: SSEエンドポイントの実装
**ファイル:** `backend/app/api/routes.py` に追加

```python
from fastapi.responses import StreamingResponse
from app.schemas.agent import AgentQueryRequest
from app.agent.mock_orchestrator import MockAgentOrchestrator

# 既存のルーターに追加
@router.post("/agent/query-stream")
async def agent_query_stream(request: AgentQueryRequest):
    """
    エージェントクエリ（SSEストリーミング）

    進捗状況をリアルタイムで返す（モック版）
    """
    orchestrator = MockAgentOrchestrator()

    async def generate():
        try:
            async for event in orchestrator.execute_query_stream(
                request.user_id, request.query
            ):
                # ProgressEventをJSON化してSSEフォーマットで送信
                yield f"data: {event.model_dump_json()}\n\n"
        except Exception as e:
            # エラー時もSSEで送信
            error_event = ProgressEvent(
                type=ProgressEventType.ERROR, message=str(e)
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx buffering無効化
        },
    )
```

**確認方法:**
```bash
# サーバー起動
cd backend
python main.py

# 別ターミナルでテスト
curl -N -X POST http://localhost:8000/api/v1/agent/query-stream \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "query": "テスト"}'

# 出力例:
# data: {"type":"thinking","message":"ユーザー情報を取得中..."}
#
# data: {"type":"function_call","tool_name":"search_customers","message":"顧客を検索中..."}
# ...
```

---

### ステップ1-3: フロントエンドの実装（1-1.5時間）

#### タスク5: カスタムフックの作成
**ファイル:** `frontend/src/hooks/useAgentStream.ts`

```typescript
'use client'

import { useState, useCallback, useRef } from 'react'
import { ProgressEvent } from '@/types/agent'

interface AgentStreamState {
  events: ProgressEvent[]
  currentMessage: string
  finalResponse: string | null
  isLoading: boolean
  error: string | null
}

export function useAgentStream() {
  const [state, setState] = useState<AgentStreamState>({
    events: [],
    currentMessage: '',
    finalResponse: null,
    isLoading: false,
    error: null,
  })

  const eventSourceRef = useRef<EventSource | null>(null)

  const sendQuery = useCallback(async (userId: string, query: string) => {
    // 既存の接続をクローズ
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }

    // 状態リセット
    setState({
      events: [],
      currentMessage: '',
      finalResponse: null,
      isLoading: true,
      error: null,
    })

    try {
      // SSEリクエストを送信
      const response = await fetch('/api/v1/agent/query-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_id: userId, query }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('Response body is null')
      }

      // ストリームを読み取る
      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.substring(6)
            try {
              const progressEvent: ProgressEvent = JSON.parse(data)

              setState((prev) => {
                const newState = {
                  ...prev,
                  events: [...prev.events, progressEvent],
                }

                // イベントタイプに応じて状態を更新
                if (progressEvent.type === 'final_response') {
                  newState.finalResponse = progressEvent.content || null
                  newState.isLoading = false
                  newState.currentMessage = ''
                } else if (progressEvent.type === 'error') {
                  newState.error = progressEvent.message || 'エラーが発生しました'
                  newState.isLoading = false
                  newState.currentMessage = ''
                } else if (progressEvent.message) {
                  newState.currentMessage = progressEvent.message
                }

                return newState
              })
            } catch (e) {
              console.error('Failed to parse SSE data:', e)
            }
          }
        }
      }
    } catch (error) {
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'エラーが発生しました',
      }))
    }
  }, [])

  const reset = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
    }
    setState({
      events: [],
      currentMessage: '',
      finalResponse: null,
      isLoading: false,
      error: null,
    })
  }, [])

  return { ...state, sendQuery, reset }
}
```

---

#### タスク6: 進捗表示コンポーネントの作成
**ファイル:** `frontend/src/components/agent/AgentProgress.tsx`

```typescript
import { ProgressEvent } from '@/types/agent'
import { CheckCircle, Loader2 } from 'lucide-react'

interface AgentProgressProps {
  events: ProgressEvent[]
  currentMessage: string
}

export function AgentProgress({ events, currentMessage }: AgentProgressProps) {
  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
      {/* 現在の進捗メッセージ */}
      {currentMessage && (
        <div className="flex items-center space-x-2 text-blue-700">
          <Loader2 className="w-4 h-4 animate-spin" />
          <span className="text-sm font-medium">{currentMessage}</span>
        </div>
      )}

      {/* 進捗履歴 */}
      {events.length > 0 && (
        <div className="space-y-1.5 border-t border-blue-200 pt-3">
          {events.map((event, idx) => (
            <ProgressEventItem key={idx} event={event} />
          ))}
        </div>
      )}
    </div>
  )
}

function ProgressEventItem({ event }: { event: ProgressEvent }) {
  switch (event.type) {
    case 'function_call':
      return (
        <div className="flex items-start space-x-2">
          <Loader2 className="w-3 h-3 text-blue-500 mt-0.5 flex-shrink-0 animate-spin" />
          <div className="text-xs text-gray-600">
            <span className="font-medium">{event.tool_name}</span>を実行中
            {event.arguments && (
              <span className="text-gray-500 ml-1">
                ({Object.entries(event.arguments).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join(', ')})
              </span>
            )}
          </div>
        </div>
      )

    case 'function_result':
      return (
        <div className="flex items-start space-x-2">
          <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
          <div className="text-xs text-green-700">
            {event.result}
          </div>
        </div>
      )

    case 'thinking':
      return (
        <div className="flex items-start space-x-2">
          <Loader2 className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0 animate-spin" />
          <div className="text-xs text-gray-500 italic">
            {event.message}
          </div>
        </div>
      )

    case 'error':
      return (
        <div className="flex items-start space-x-2">
          <span className="text-red-500 text-xs mt-0.5">✗</span>
          <div className="text-xs text-red-600">
            {event.message}
          </div>
        </div>
      )

    default:
      return null
  }
}
```

---

#### タスク7: チャットUIへの統合
**ファイル:** `frontend/src/components/chat/ChatMessages.tsx` を更新

```typescript
'use client'

import { useEffect, useRef } from 'react'
import { ChatMessage } from './ChatMessage'
import { AgentProgress } from '../agent/AgentProgress'
import { AlertCircle } from 'lucide-react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  error: string | null
  // エージェント進捗用の新しいprops
  agentEvents?: any[]
  agentCurrentMessage?: string
}

export function ChatMessages({
  messages,
  isLoading,
  error,
  agentEvents = [],
  agentCurrentMessage = '',
}: ChatMessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 新しいメッセージが追加されたら自動スクロール
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading, agentEvents])

  return (
    <main className="flex-1 overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        {/* メッセージ履歴 */}
        {messages.map((message, idx) => (
          <ChatMessage
            key={idx}
            role={message.role}
            content={message.content}
          />
        ))}

        {/* エージェント進捗表示（ローディング中のみ） */}
        {isLoading && (agentEvents.length > 0 || agentCurrentMessage) && (
          <div className="mb-6">
            <AgentProgress
              events={agentEvents}
              currentMessage={agentCurrentMessage}
            />
          </div>
        )}

        {/* 従来のローディング表示（エージェント進捗がない場合） */}
        {isLoading && agentEvents.length === 0 && !agentCurrentMessage && (
          <div className="flex items-center space-x-2 text-gray-600 mb-4">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
            <span>回答を生成中...</span>
          </div>
        )}

        {/* エラー表示 */}
        {error && (
          <div className="flex items-start space-x-3 bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-4">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">エラーが発生しました</p>
              <p className="text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* 自動スクロール用の要素 */}
        <div ref={messagesEndRef} />
      </div>
    </main>
  )
}
```

---

#### タスク8: ページコンポーネントの更新
**ファイル:** `frontend/src/app/page.tsx` を更新

```typescript
'use client'

import { useState } from 'react'
import { ChatMessages } from '@/components/chat/ChatMessages'
import { ChatInput } from '@/components/chat/ChatInput'
import { useAgentStream } from '@/hooks/useAgentStream'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const {
    events: agentEvents,
    currentMessage: agentCurrentMessage,
    finalResponse,
    isLoading,
    error,
    sendQuery,
  } = useAgentStream()

  const handleSendMessage = async (content: string) => {
    // ユーザーメッセージを追加
    const userMessage: Message = { role: 'user', content }
    setMessages((prev) => [...prev, userMessage])

    // エージェントクエリを送信
    await sendQuery('1', content)
  }

  // 最終レスポンスが来たらメッセージに追加
  useEffect(() => {
    if (finalResponse) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: finalResponse },
      ])
    }
  }, [finalResponse])

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4">
        <h1 className="text-xl font-semibold text-gray-800">営業コパイロット</h1>
      </header>

      <ChatMessages
        messages={messages}
        isLoading={isLoading}
        error={error}
        agentEvents={agentEvents}
        agentCurrentMessage={agentCurrentMessage}
      />

      <ChatInput onSendMessage={handleSendMessage} disabled={isLoading} />
    </div>
  )
}
```

---

### ステップ1-4: 動作確認（30分）

#### タスク9: ローカルでの動作確認

**手順:**
1. バックエンド起動
   ```bash
   cd backend
   python main.py
   ```

2. フロントエンド起動
   ```bash
   cd frontend
   npm run dev
   ```

3. ブラウザで http://localhost:3000 を開く

4. チャットで「私の担当案件を教えて」と入力

5. **期待される動作:**
   - 進捗ボックスが表示される
   - 「ユーザー情報を取得中...」→「顧客を検索中...」→「ニュースを取得中...」→「レポートを作成中...」と順次表示
   - 各ステップの完了が✓で表示される
   - 最終的にモックレスポンスがMarkdown形式で表示される

**チェックリスト:**
- [ ] SSEが正しく送信されている（devtoolsのNetworkタブで確認）
- [ ] 進捗メッセージが順次表示される
- [ ] ツール呼び出しと結果が表示される
- [ ] 最終レスポンスがMarkdown形式で表示される
- [ ] エラー時も適切に表示される

---

## フェーズ2: 実際のエージェント統合（エージェント実装後）

### ステップ2-1: モックから実際のオーケストレーターに切り替え

**ファイル:** `backend/app/agent/orchestrator.py` を作成

```python
"""実際のエージェントオーケストレーター"""

from typing import AsyncIterator
from app.schemas.agent import ProgressEvent, ProgressEventType
from app.agent.tools import execute_tool

class SalesAgentOrchestrator:
    """営業エージェント（実装版）"""

    async def execute_query_stream(
        self, user_id: str, query: str
    ) -> AsyncIterator[ProgressEvent]:
        """実際のFunction Callingを実行"""

        # ステップ1: ユーザー情報取得
        yield ProgressEvent(
            type=ProgressEventType.THINKING,
            message="ユーザー情報を取得中..."
        )

        # ステップ2: Gemini APIでFunction Callingループ
        iteration = 0
        max_iterations = 10
        conversation_history = []

        while iteration < max_iterations:
            iteration += 1

            # Gemini APIを呼び出し
            response = await self._call_gemini(query, conversation_history)

            # Function Callがあるかチェック
            if self._has_function_call(response):
                function_call = self._extract_function_call(response)

                # ツール呼び出しイベント
                yield ProgressEvent(
                    type=ProgressEventType.FUNCTION_CALL,
                    tool_name=function_call.name,
                    arguments=dict(function_call.args),
                    message=self._get_tool_message(function_call.name)
                )

                # ツールを実行
                result = await execute_tool(function_call.name, function_call.args)

                # ツール実行結果イベント
                yield ProgressEvent(
                    type=ProgressEventType.FUNCTION_RESULT,
                    tool_name=function_call.name,
                    result=self._format_result(result)
                )

                # 会話履歴に追加
                conversation_history.append(...)

            else:
                # 最終レスポンス
                final_text = self._extract_text(response)

                yield ProgressEvent(
                    type=ProgressEventType.FINAL_RESPONSE,
                    content=final_text
                )
                break
```

**ファイル:** `backend/app/api/routes.py` を更新

```python
# MockAgentOrchestrator → SalesAgentOrchestrator に変更
from app.agent.orchestrator import SalesAgentOrchestrator

@router.post("/agent/query-stream")
async def agent_query_stream(request: AgentQueryRequest):
    orchestrator = SalesAgentOrchestrator()  # モックから実装版に変更
    # 以下同じ
```

---

## 実装スケジュール

### Day 1: スキーマとモック（2-3時間）
- [x] バックエンド型定義
- [x] フロントエンド型定義
- [x] モックオーケストレーター
- [x] SSEエンドポイント

### Day 2: フロントエンド実装（1.5-2時間）
- [x] カスタムフック
- [x] 進捗表示コンポーネント
- [x] チャットUI統合

### Day 3: 動作確認とUI調整（0.5-1時間）
- [x] ローカルテスト
- [x] UI/UXの微調整
- [x] エラーハンドリング確認

### 後日: 実際のエージェント統合（エージェント実装後）
- [ ] オーケストレーター実装
- [ ] モックから実装版に切り替え
- [ ] エンドツーエンドテスト

---

## 成果物チェックリスト

### バックエンド
- [ ] `app/schemas/agent.py` - 型定義
- [ ] `app/agent/mock_orchestrator.py` - モック実装
- [ ] `app/api/routes.py` - SSEエンドポイント追加
- [ ] curlでSSEが受信できることを確認

### フロントエンド
- [ ] `src/types/agent.ts` - 型定義
- [ ] `src/hooks/useAgentStream.ts` - カスタムフック
- [ ] `src/components/agent/AgentProgress.tsx` - 進捗表示
- [ ] `src/components/chat/ChatMessages.tsx` - UI統合
- [ ] `src/app/page.tsx` - ページ更新
- [ ] ブラウザで進捗が表示されることを確認

### ドキュメント
- [x] `docs/16_agent_progress_communication.md` - 設計書
- [x] `docs/17_agent_progress_implementation_plan.md` - 実装プラン

---

## 次のアクション

**今すぐ開始:**
1. `backend/app/schemas/agent.py` の作成
2. `frontend/src/types/agent.ts` の作成
3. モックオーケストレーターの実装

**確認ポイント:**
- 各ステップごとに動作確認
- SSEが正しく送受信されているか
- UIが意図通りに表示されているか

このプランに従って実装を進めましょう。
