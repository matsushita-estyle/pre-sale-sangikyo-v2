# エージェント進捗状況の通信設計

**日付:** 2026-03-01
**概要:** Function Calling実装前に、エージェントの動作状況をフロントエンドに伝える仕組みを設計

---

## 1. 要件

### 1.1 表示したい情報
エージェントが以下のような処理を行う際に、ユーザーに進捗を見せたい：

1. **ツール呼び出し**
   - 「顧客を検索中...」
   - 「ニュースを取得中...」
   - 「製品情報を検索中...」

2. **思考過程**
   - 「データを分析中...」
   - 「レポートを作成中...」

3. **完了状態**
   - 「完了しました」

### 1.2 参考: sample-sales-agent-demo

sample-sales-agent-demoでは、以下のような進捗情報を送信している：

```python
# orchestrator.py内
await on_step({
    "type": "function_call",
    "tool_name": "search_customers",
    "arguments": {"industries": ["IT"]}
})

await on_step({
    "type": "function_result",
    "tool_name": "search_customers",
    "result": "3件の顧客が見つかりました"
})

await on_step({
    "type": "thinking",
    "message": "レポートを作成中..."
})

await on_step({
    "type": "final_response",
    "message": "完了しました"
})
```

---

## 2. 通信方式の選択

### 2.1 選択肢の比較

#### オプション1: Server-Sent Events (SSE) ⭐ 推奨
**メリット:**
- リアルタイム送信（サーバー→クライアント）
- 標準的な技術（EventSource API）
- 実装が比較的シンプル
- sample-sales-agent-demoと同じ方式

**デメリット:**
- 単方向通信のみ（サーバー→クライアント）
- 古いブラウザでは非対応

**実装例:**
```python
# FastAPI
from fastapi.responses import StreamingResponse

async def generate_progress():
    yield f"data: {json.dumps({'type': 'thinking', 'message': '顧客を検索中...'})}\n\n"
    yield f"data: {json.dumps({'type': 'function_call', 'tool': 'search_customers'})}\n\n"
    yield f"data: {json.dumps({'type': 'response', 'content': '完了しました'})}\n\n"

@router.post("/sales-agent/query-stream")
async def query_stream(request: QueryRequest):
    return StreamingResponse(generate_progress(), media_type="text/event-stream")
```

```typescript
// React
const eventSource = new EventSource('/api/v1/sales-agent/query-stream')
eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data)
    console.log(data.type, data.message)
}
```

---

#### オプション2: WebSocket
**メリット:**
- 双方向通信
- リアルタイム性が高い

**デメリット:**
- 実装が複雑
- インフラの設定が必要（Azure WebSocketsサポート）
- オーバースペック（今回は単方向で十分）

---

#### オプション3: ポーリング
**メリット:**
- シンプル

**デメリット:**
- リアルタイム性が低い
- サーバー負荷が高い
- UX が悪い

---

### 2.2 決定: Server-Sent Events (SSE)

**理由:**
- sample-sales-agent-demoと同じ方式
- リアルタイム性が高い
- 実装がシンプル
- 今回のユースケースに最適（サーバー→クライアント単方向）

---

## 3. データフォーマット設計

### 3.1 進捗イベントの型定義

#### バックエンド（Python）
```python
# app/schemas/agent.py
from enum import Enum
from pydantic import BaseModel

class ProgressEventType(str, Enum):
    """進捗イベントの種類"""
    THINKING = "thinking"              # 思考中
    FUNCTION_CALL = "function_call"    # ツール呼び出し
    FUNCTION_RESULT = "function_result" # ツール実行結果
    RESPONSE_CHUNK = "response_chunk"  # レスポンス（部分）
    FINAL_RESPONSE = "final_response"  # 最終レスポンス
    ERROR = "error"                    # エラー

class ProgressEvent(BaseModel):
    """進捗イベント"""
    type: ProgressEventType
    message: str | None = None
    tool_name: str | None = None
    arguments: dict | None = None
    result: str | None = None
    content: str | None = None
```

#### フロントエンド（TypeScript）
```typescript
// types/agent.ts
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
```

### 3.2 送信イベントの例

#### イベント1: ツール呼び出し
```json
{
  "type": "function_call",
  "tool_name": "search_customers",
  "arguments": {
    "industries": ["IT", "通信"]
  },
  "message": "顧客を検索中..."
}
```

#### イベント2: ツール実行結果
```json
{
  "type": "function_result",
  "tool_name": "search_customers",
  "result": "3件の顧客が見つかりました"
}
```

#### イベント3: 思考中
```json
{
  "type": "thinking",
  "message": "データを分析中..."
}
```

#### イベント4: レスポンス（部分）
```json
{
  "type": "response_chunk",
  "content": "## 担当案件一覧\n\n"
}
```

#### イベント5: 最終レスポンス
```json
{
  "type": "final_response",
  "content": "## 担当案件一覧\n\n### KDDI株式会社\n..."
}
```

#### イベント6: エラー
```json
{
  "type": "error",
  "message": "APIクォータ制限に達しました。1分後に再試行してください。"
}
```

---

## 4. バックエンド実装設計

### 4.1 オーケストレーター設計

```python
# app/agent/orchestrator.py
from typing import AsyncIterator
from app.schemas.agent import ProgressEvent, ProgressEventType

class SalesAgentOrchestrator:
    """営業エージェントのオーケストレーター"""

    async def execute_query_stream(
        self,
        user_id: str,
        query: str
    ) -> AsyncIterator[ProgressEvent]:
        """
        クエリを実行し、進捗状況をストリームで返す

        Yields:
            ProgressEvent: 進捗イベント
        """
        try:
            # ステップ1: ユーザー情報取得
            yield ProgressEvent(
                type=ProgressEventType.THINKING,
                message="ユーザー情報を取得中..."
            )

            # ステップ2: Function Callingループ
            iteration = 0
            max_iterations = 10

            while iteration < max_iterations:
                iteration += 1

                # Gemini APIを呼び出し
                response = await self._call_gemini(query, conversation_history)

                # Function Callがあるかチェック
                if response.candidates[0].content.parts[0].function_call:
                    function_call = response.candidates[0].content.parts[0].function_call

                    # ツール呼び出しイベント
                    yield ProgressEvent(
                        type=ProgressEventType.FUNCTION_CALL,
                        tool_name=function_call.name,
                        arguments=dict(function_call.args),
                        message=self._get_tool_message(function_call.name)
                    )

                    # ツールを実行
                    result = await self._execute_tool(function_call.name, function_call.args)

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
                    final_text = response.candidates[0].content.parts[0].text

                    yield ProgressEvent(
                        type=ProgressEventType.FINAL_RESPONSE,
                        content=final_text
                    )
                    break

        except Exception as e:
            yield ProgressEvent(
                type=ProgressEventType.ERROR,
                message=str(e)
            )

    def _get_tool_message(self, tool_name: str) -> str:
        """ツール名から表示メッセージを生成"""
        messages = {
            "get_user_attributes": "ユーザー情報を取得中...",
            "search_customers": "顧客を検索中...",
            "search_products": "製品を検索中...",
            "search_latest_news": "最新ニュースを取得中...",
        }
        return messages.get(tool_name, f"{tool_name}を実行中...")

    def _format_result(self, result: Any) -> str:
        """ツール実行結果を表示用にフォーマット"""
        if isinstance(result, list):
            return f"{len(result)}件のデータが見つかりました"
        return "完了しました"
```

### 4.2 APIエンドポイント設計

```python
# app/api/routes.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json

router = APIRouter()

@router.post("/sales-agent/query-stream")
async def query_stream(
    request: QueryRequest,
    agent: SalesAgentOrchestrator = Depends(get_agent)
):
    """
    エージェントクエリ（SSEストリーミング）

    進捗状況をリアルタイムで返す
    """
    async def generate():
        async for event in agent.execute_query_stream(request.user_id, request.query):
            # ProgressEventをJSON化してSSEフォーマットで送信
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
```

---

## 5. フロントエンド実装設計

### 5.1 カスタムフックの設計

```typescript
// hooks/useAgentStream.ts
import { useState, useCallback } from 'react'
import { ProgressEvent } from '@/types/agent'

interface AgentStreamState {
  events: ProgressEvent[]
  currentMessage: string
  isLoading: boolean
  error: string | null
}

export function useAgentStream() {
  const [state, setState] = useState<AgentStreamState>({
    events: [],
    currentMessage: '',
    isLoading: false,
    error: null,
  })

  const sendQuery = useCallback(async (userId: string, query: string) => {
    setState({
      events: [],
      currentMessage: '',
      isLoading: true,
      error: null,
    })

    const eventSource = new EventSource(
      `/api/v1/sales-agent/query-stream?user_id=${userId}&query=${encodeURIComponent(query)}`
    )

    eventSource.onmessage = (event) => {
      const progressEvent: ProgressEvent = JSON.parse(event.data)

      setState((prev) => ({
        ...prev,
        events: [...prev.events, progressEvent],
        currentMessage: progressEvent.message || prev.currentMessage,
      }))

      // 最終レスポンスまたはエラーで終了
      if (progressEvent.type === 'final_response' || progressEvent.type === 'error') {
        eventSource.close()
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: progressEvent.type === 'error' ? progressEvent.message || null : null,
        }))
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setState((prev) => ({
        ...prev,
        isLoading: false,
        error: 'ストリームエラーが発生しました',
      }))
    }
  }, [])

  return { ...state, sendQuery }
}
```

### 5.2 進捗表示コンポーネント

```typescript
// components/agent/AgentProgress.tsx
import { ProgressEvent } from '@/types/agent'

interface AgentProgressProps {
  events: ProgressEvent[]
  currentMessage: string
}

export function AgentProgress({ events, currentMessage }: AgentProgressProps) {
  return (
    <div className="space-y-2">
      {/* 現在の進捗メッセージ */}
      {currentMessage && (
        <div className="flex items-center space-x-2 text-blue-600">
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
          <span className="text-sm font-medium">{currentMessage}</span>
        </div>
      )}

      {/* 進捗履歴 */}
      <div className="space-y-1">
        {events.map((event, idx) => (
          <ProgressEventItem key={idx} event={event} />
        ))}
      </div>
    </div>
  )
}

function ProgressEventItem({ event }: { event: ProgressEvent }) {
  switch (event.type) {
    case 'function_call':
      return (
        <div className="text-xs text-gray-500">
          ✓ {event.message}
        </div>
      )

    case 'function_result':
      return (
        <div className="text-xs text-green-600">
          → {event.result}
        </div>
      )

    case 'thinking':
      return (
        <div className="text-xs text-gray-400 italic">
          {event.message}
        </div>
      )

    default:
      return null
  }
}
```

### 5.3 チャットコンポーネントの統合

```typescript
// components/chat/ChatInterface.tsx
import { useAgentStream } from '@/hooks/useAgentStream'
import { AgentProgress } from '@/components/agent/AgentProgress'

export function ChatInterface() {
  const { events, currentMessage, isLoading, error, sendQuery } = useAgentStream()

  const handleSubmit = (query: string) => {
    sendQuery('1', query)
  }

  return (
    <div>
      {/* メッセージ履歴 */}
      <div className="messages">
        {/* ... */}
      </div>

      {/* エージェント進捗表示 */}
      {isLoading && (
        <AgentProgress events={events} currentMessage={currentMessage} />
      )}

      {/* エラー表示 */}
      {error && (
        <div className="text-red-600">{error}</div>
      )}

      {/* 入力フォーム */}
      <form onSubmit={(e) => { e.preventDefault(); handleSubmit(input) }}>
        <input type="text" />
        <button type="submit">送信</button>
      </form>
    </div>
  )
}
```

---

## 6. UI/UXデザイン案

### 6.1 進捗表示のビジュアル

#### パターン1: シンプルなローディングメッセージ
```
[スピナー] 顧客を検索中...
```

#### パターン2: ステップ表示
```
✓ ユーザー情報を取得
✓ 顧客を検索中... → 3件の顧客が見つかりました
⏳ レポートを作成中...
```

#### パターン3: タイムライン表示
```
10:30:01 - ユーザー情報を取得
10:30:02 - 顧客を検索 (3件)
10:30:03 - ニュースを取得 (5件)
10:30:05 - レポート作成中...
```

### 6.2 推奨デザイン

**パターン2（ステップ表示）を推奨**

**理由:**
- ユーザーがエージェントの処理を理解しやすい
- 完了したステップが可視化される
- シンプルで見やすい

**実装例:**
```tsx
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-2">
  {/* 現在の進捗 */}
  <div className="flex items-center space-x-2">
    <Spinner className="w-4 h-4 text-blue-600" />
    <span className="text-sm font-medium text-blue-800">
      顧客を検索中...
    </span>
  </div>

  {/* 完了済みステップ */}
  <div className="space-y-1">
    <div className="flex items-center space-x-2 text-xs text-green-600">
      <CheckIcon className="w-3 h-3" />
      <span>ユーザー情報を取得しました</span>
    </div>
  </div>
</div>
```

---

## 7. 実装順序

### ステップ1: スキーマ定義（30分）
- `app/schemas/agent.py` - ProgressEvent定義
- `frontend/src/types/agent.ts` - TypeScript型定義

### ステップ2: バックエンド基盤（1時間）
- `app/agent/orchestrator.py` - モックでストリーム生成
- `app/api/routes.py` - SSEエンドポイント実装

### ステップ3: フロントエンド基盤（1時間）
- `hooks/useAgentStream.ts` - カスタムフック
- `components/agent/AgentProgress.tsx` - 進捗表示

### ステップ4: 統合テスト（30分）
- ローカルで動作確認
- モックデータでストリーム表示確認

### ステップ5: 実際のエージェント実装に統合（エージェント実装後）
- オーケストレーターに実際のFunction Calling実装
- ツール呼び出しごとにイベント送信

---

## 8. まとめ

### 8.1 技術選定
- ✅ **SSE（Server-Sent Events）**を採用
- ✅ **ProgressEvent型**で統一されたデータフォーマット
- ✅ **EventSource API**でフロントエンド受信

### 8.2 実装ポイント
- バックエンド: `AsyncIterator[ProgressEvent]` でイベントをyield
- フロントエンド: カスタムフックで状態管理
- UI: ステップ表示でユーザーフレンドリー

### 8.3 次のアクション
1. スキーマ定義の作成
2. モックストリームの実装
3. フロントエンド受信の実装
4. UI/UX確認
5. 実際のエージェント実装に統合

この設計により、エージェントがどのように動いているかをユーザーにリアルタイムで伝えることができます。
