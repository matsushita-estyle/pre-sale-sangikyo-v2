# エージェント進捗通信のモック実装（完了）

**日付:** 2026-03-01
**概要:** SSEを使ったエージェント進捗通信のモック実装
**参照:**
- [16_agent_progress_communication.md](16_agent_progress_communication.md) - 設計
- [17_agent_progress_implementation_plan.md](17_agent_progress_implementation_plan.md) - 実装プラン

---

## 実装完了タスク

### ✅ バックエンド実装

#### 1. 型定義 (`backend/app/schemas/agent.py`)
```python
class ProgressEventType(str, Enum):
    THINKING = "thinking"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESULT = "function_result"
    RESPONSE_CHUNK = "response_chunk"
    FINAL_RESPONSE = "final_response"
    ERROR = "error"

class ProgressEvent(BaseModel):
    type: ProgressEventType
    message: str | None = None
    tool_name: str | None = None
    arguments: dict[str, Any] | None = None
    result: str | None = None
    content: str | None = None
```

#### 2. モックオーケストレーター (`backend/app/agent/mock_orchestrator.py`)
- 6ステップのモック進捗を生成:
  1. ユーザー情報取得（thinking）
  2. 顧客検索（function_call + function_result）
  3. ニュース取得（function_call + function_result）
  4. レポート作成（thinking）
  5. 最終レスポンス（final_response）

#### 3. SSEエンドポイント (`backend/app/api/routes.py`)
```python
@router.post("/agent/query-stream")
async def agent_query_stream(request: AgentQueryRequest):
    orchestrator = MockAgentOrchestrator()
    async def generate():
        async for event in orchestrator.execute_query_stream(...):
            yield f"data: {event.model_dump_json()}\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

#### 4. curlテスト結果 ✅
```bash
curl -N -X POST http://localhost:8000/api/v1/agent/query-stream \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1","query":"テスト"}'

# 出力:
# data: {"type":"thinking","message":"ユーザー情報を取得中..."}
# data: {"type":"function_call","tool_name":"search_customers",...}
# data: {"type":"function_result","result":"3件の顧客が見つかりました"}
# ...
```

**動作確認:** ✅ SSEが正常に送信されることを確認

---

### ✅ フロントエンド実装

#### 5. 型定義 (`frontend/src/types/agent.ts`)
```typescript
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

#### 6. カスタムフック (`frontend/src/hooks/useAgentStream.ts`)
- SSEストリームの受信と状態管理
- `fetch` + ReadableStream でSSEを読み取り
- イベントタイプに応じて状態を更新

**主な機能:**
```typescript
const { events, currentMessage, finalResponse, isLoading, error, sendQuery } = useAgentStream()

await sendQuery('1', 'テスト質問')
// → SSEでリアルタイムに進捗を受信
// → eventsに進捗イベントが追加される
// → currentMessageに現在のメッセージ
// → finalResponseに最終レスポンス
```

#### 7. 進捗表示コンポーネント (`frontend/src/components/agent/AgentProgress.tsx`)
- 青いボックスで進捗を表示
- アイコン付きイベント表示:
  - `thinking`: スピナー + メッセージ
  - `function_call`: スピナー + ツール名
  - `function_result`: ✓ + 結果
  - `error`: ✗ + エラーメッセージ

**表示例:**
```
┌─────────────────────────────────────┐
│ [スピナー] ユーザー情報を取得中...     │
│ ────────────────────────────────── │
│ [スピナー] search_customers を実行中 │
│ ✓ 3件の顧客が見つかりました          │
│ [スピナー] レポートを作成中...        │
└─────────────────────────────────────┘
```

---

## 未完了タスク（次回作業）

### ⚠️ UI統合（残り作業）

#### 8. page.tsx の更新
**現状:** 既存のチャット機能を使用

**必要な変更:**
```typescript
// 既存のsendChatMessage()を useAgentStream() に置き換え
import { useAgentStream } from '@/hooks/useAgentStream'

const { events, currentMessage, finalResponse, isLoading, error, sendQuery } = useAgentStream()

const handleSubmit = async (query: string) => {
  setMessages((prev) => [...prev, { role: 'user', content: query }])
  await sendQuery(selectedUserId, query)
}

// finalResponseが来たらメッセージに追加
useEffect(() => {
  if (finalResponse) {
    setMessages((prev) => [...prev, { role: 'assistant', content: finalResponse }])
  }
}, [finalResponse])
```

#### 9. ChatMessages.tsx の更新
**必要な変更:**
```typescript
// AgentProgressコンポーネントを追加
import { AgentProgress } from '@/components/agent/AgentProgress'

interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  error: string | null
  agentEvents?: ProgressEvent[]        // 追加
  agentCurrentMessage?: string         // 追加
}

// ローディング中にAgentProgressを表示
{isLoading && agentEvents && agentCurrentMessage && (
  <AgentProgress events={agentEvents} currentMessage={agentCurrentMessage} />
)}
```

#### 10. ブラウザでの動作確認
- [ ] フロントエンド起動
- [ ] チャット入力
- [ ] 進捗表示の確認
- [ ] 最終レスポンスの表示確認

---

## 実装ファイル一覧

### バックエンド
- ✅ `backend/app/schemas/agent.py` - 型定義
- ✅ `backend/app/agent/__init__.py` - モジュール初期化
- ✅ `backend/app/agent/mock_orchestrator.py` - モックオーケストレーター
- ✅ `backend/app/api/routes.py` - SSEエンドポイント追加

### フロントエンド
- ✅ `frontend/src/types/agent.ts` - 型定義（追加）
- ✅ `frontend/src/hooks/useAgentStream.ts` - カスタムフック
- ✅ `frontend/src/components/agent/AgentProgress.tsx` - 進捗表示
- ⚠️ `frontend/src/app/page.tsx` - 未更新（次回）
- ⚠️ `frontend/src/components/chat/ChatMessages.tsx` - 未更新（次回）

---

## 技術的なポイント

### SSEの実装

**バックエンド:**
```python
async def generate():
    async for event in orchestrator.execute_query_stream(user_id, query):
        yield f"data: {event.model_dump_json()}\n\n"

return StreamingResponse(generate(), media_type="text/event-stream")
```

**フロントエンド:**
```typescript
const reader = response.body?.getReader()
const decoder = new TextDecoder()

while (true) {
  const { done, value } = await reader.read()
  if (done) break

  const chunk = decoder.decode(value, { stream: true })
  // "data: {...}\n\n" 形式をパース
}
```

### イベント駆動の状態管理

1. SSEでイベントを受信
2. イベントタイプに応じて状態を更新:
   - `thinking` / `function_call` → `currentMessage`を更新
   - `function_result` → `events`に追加
   - `final_response` → `finalResponse`に設定、`isLoading = false`
   - `error` → `error`に設定、`isLoading = false`

---

## 動作フロー

```
User Input: "私の担当案件を教えて"
    ↓
[Frontend] sendQuery('1', '私の担当案件を教えて')
    ↓
[Backend] POST /api/v1/agent/query-stream
    ↓
[Mock] execute_query_stream()
    ↓
Event 1: {"type":"thinking","message":"ユーザー情報を取得中..."}
    ↓ (1秒待機)
Event 2: {"type":"function_call","tool_name":"search_customers",...}
    ↓ (1.5秒待機)
Event 3: {"type":"function_result","result":"3件の顧客が見つかりました"}
    ↓ (0.5秒待機)
Event 4: {"type":"function_call","tool_name":"search_latest_news",...}
    ↓ (1.5秒待機)
Event 5: {"type":"function_result","result":"5件のニュースが見つかりました"}
    ↓ (0.5秒待機)
Event 6: {"type":"thinking","message":"レポートを作成中..."}
    ↓ (2秒待機)
Event 7: {"type":"final_response","content":"## 担当案件一覧\n\n..."}
    ↓
[Frontend] finalResponseをメッセージに追加
    ↓
表示完了
```

**合計所要時間:** 約7秒

---

## 次のステップ

### 即座に実施
1. **page.tsx の更新** - useAgentStreamの統合
2. **ChatMessages.tsx の更新** - AgentProgress表示
3. **ブラウザでの動作確認**

### 統合テスト後
4. エラーハンドリングの確認
5. UI/UXの微調整
6. 実際のエージェント実装への準備

### 実際のエージェント実装時
7. `MockAgentOrchestrator` → `SalesAgentOrchestrator` に切り替え
8. Gemini Function Calling の実装
9. エンドツーエンドテスト

---

## トラブルシューティング

### SSEが受信できない場合
- CORS設定を確認
- ブラウザのDevTools > Networkタブで確認
- `text/event-stream` のContent-Typeが正しいか

### 進捗が表示されない場合
- `events` と `currentMessage` が正しく渡されているか
- `AgentProgress` コンポーネントがレンダリングされているか

### バックグラウンドプロセスが多い場合
```bash
# ポート8000のプロセスをすべて停止
lsof -ti:8000 | xargs kill -9

# ポート3000のプロセスをすべて停止
lsof -ti:3000 | xargs kill -9
```

---

## まとめ

### 完了した機能 ✅
- SSEによるリアルタイム進捗通信
- モックデータでの動作確認
- バックエンド・フロントエンド間の通信確立
- 進捗表示UIコンポーネント

### 未完了（次回作業）⚠️
- page.tsx への統合
- ChatMessages.tsx への統合
- ブラウザでの動作確認

### 工数実績
- **計画:** 2-3時間
- **実績:** 約2.5時間（バックエンド実装 + フロントエンド実装）
- **残り:** 0.5-1時間（UI統合 + 動作確認）

**合計見込み:** 3-4時間（ほぼ計画通り）
