# 会話履歴機能 実装計画

**作成日**: 2026-03-01
**対象**: pre-sale-sangikyo-v2
**アーキテクチャ**: ハイブリッド (セッションIDベース)
**見積もり工数**: 10-15時間 (最小構成: 3時間)

---

## 概要

現在、Agentは各リクエストを独立して処理しており、会話履歴を保持していません。このため、ユーザーが「上記の中で金額が多いのは?」のような前の会話を参照する質問をすると回答できません。

この計画では、**会話ごとにconversation_idを発行し、DBに履歴を保存**する方式で会話履歴機能を実装します。フロントエンドは会話IDだけ送り、バックエンドが履歴を復元してGeminiに渡します。

---

## アーキテクチャ選択

### 選択肢の比較

| 方式 | メリット | デメリット |
|------|---------|-----------|
| **ステートレス** | バックエンドがシンプル、スケーラブル | 毎回全履歴を送信、ネットワーク負荷増 |
| **ステートフル** | ネットワーク効率的、履歴の一元管理 | バックエンドの複雑性増、永続化が必要 |
| **ハイブリッド (推奨)** | バランスが良い、履歴の永続化が可能 | 実装が複雑 |

### 採用: ハイブリッド (セッションIDベース)

**理由**:
- 将来的な履歴閲覧機能も見据えて
- ネットワーク効率とスケーラビリティのバランス
- Cosmos DBで履歴を一元管理

---

## 実装フェーズ (全10フェーズ)

### Phase 1: データモデル作成 (30分)

**ファイル作成**: `backend/app/models/conversation.py`

```python
from pydantic import BaseModel

class Message(BaseModel):
    """1つのメッセージ"""
    message_id: str  # UUID
    role: str  # "user" or "assistant"
    content: str
    timestamp: str  # ISO 8601
    search_history: list[dict] | None = None

class Conversation(BaseModel):
    """会話セッション全体"""
    id: str  # conversation_id (UUID) - partition key
    user_id: str
    title: str  # "KDDI案件について"など (自動生成)
    messages: list[Message]
    created_at: str
    updated_at: str
    is_active: bool = True  # アーカイブ機能用
```

**やること**:
- 上記ファイルを作成
- Cosmos DBのコンテナ `Conversations` を作成 (Azure Portal or Terraform)
- パーティションキー: `/id` (conversation_id)

---

### Phase 2: ConversationRepository 作成 (1時間)

**ファイル作成**: `backend/app/repositories/conversation.py`

```python
from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository

class ConversationRepository(BaseRepository):
    def __init__(self):
        super().__init__(container_name="Conversations")

    async def create_conversation(
        self, user_id: str, first_message: Message
    ) -> Conversation:
        """新規会話を作成"""
        conv_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            title=self._generate_title(first_message.content),
            messages=[first_message],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        await self.create_item(conversation.dict())
        return conversation

    async def get_conversation(self, conversation_id: str) -> Conversation:
        """会話を取得"""
        item = await self.get_item_by_id(conversation_id)
        return Conversation(**item)

    async def add_message(
        self, conversation_id: str, message: Message
    ) -> None:
        """会話にメッセージ追加"""
        conv = await self.get_conversation(conversation_id)
        conv.messages.append(message)
        conv.updated_at = datetime.utcnow().isoformat()
        await self.update_item(conversation_id, conv.dict())

    async def list_user_conversations(
        self, user_id: str, limit: int = 50
    ) -> list[Conversation]:
        """ユーザーの会話一覧"""
        query = f"SELECT * FROM c WHERE c.user_id = '{user_id}' AND c.is_active = true ORDER BY c.updated_at DESC OFFSET 0 LIMIT {limit}"
        items = await self.query_items(query)
        return [Conversation(**item) for item in items]

    def _generate_title(self, first_query: str) -> str:
        """最初の質問から会話タイトルを生成"""
        # Phase 10で実装: Gemini APIで要約
        return first_query[:30] + "..." if len(first_query) > 30 else first_query
```

**やること**:
- 上記メソッドを実装
- Cosmos DB の CRUD操作を実装
- エラーハンドリング追加

---

### Phase 3: Orchestrator更新 (45分)

**ファイル更新**: `backend/app/agent/orchestrator.py`

**変更箇所**: `execute_query_stream` メソッド

```python
async def execute_query_stream(
    self,
    user_id: str,
    query: str,
    conversation_history: list[dict] | None = None  # ← 追加
) -> AsyncIterator[ProgressEvent]:
    """Execute query with function calling and stream progress.

    Args:
        user_id: User ID making the query
        query: User's query string
        conversation_history: Previous conversation in Gemini format (optional)
    """
    yield ProgressEvent(
        type=ProgressEventType.THINKING, message="クエリを解析中..."
    )

    # 履歴がある場合は利用
    if conversation_history:
        chat_history = conversation_history.copy()
        # 新しいユーザークエリを追加
        chat_history.append({
            "role": "user",
            "parts": [{"text": f"ユーザーID: {user_id}\n\n{query}"}]
        })
    else:
        # 初回会話
        initial_context = f"現在のユーザーID: {user_id}\n\nユーザーからの質問: {query}"
        chat_history = [{"role": "user", "parts": [{"text": initial_context}]}]

    # ... 既存のFunction Callingループ
```

**やること**:
- パラメータ `conversation_history` を追加
- 履歴がある場合はそれを使い、新しいクエリを追加
- テスト: 履歴なしの場合も動作すること

---

### Phase 4: APIスキーマ & エンドポイント更新 (1.5時間)

#### 4-1: スキーマ更新

**ファイル更新**: `backend/app/schemas/agent.py`

```python
class AgentQueryRequest(BaseModel):
    """エージェントクエリリクエスト"""
    user_id: str
    query: str
    conversation_id: str | None = None  # ← 追加

class ConversationResponse(BaseModel):
    """会話レスポンス"""
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
```

#### 4-2: エンドポイント追加

**ファイル更新**: `backend/app/api/routes.py`

```python
from app.repositories.conversation import ConversationRepository
from app.models.conversation import Message

# 新規エンドポイント: 会話管理
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    user_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    """新規会話を開始"""
    conv_id = str(uuid.uuid4())
    first_message = Message(
        message_id=str(uuid.uuid4()),
        role="system",
        content="会話を開始しました",
        timestamp=datetime.utcnow().isoformat()
    )
    conv = await repo.create_conversation(user_id, first_message)
    return ConversationResponse(
        id=conv.id,
        user_id=conv.user_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        message_count=len(conv.messages)
    )

@router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    """会話履歴を取得"""
    return await repo.get_conversation(conversation_id)

@router.get("/users/{user_id}/conversations")
async def list_conversations(
    user_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    """会話一覧取得"""
    return await repo.list_user_conversations(user_id)
```

#### 4-3: 既存エンドポイント更新

```python
# ヘルパー関数
def convert_to_gemini_format(messages: list[Message]) -> list[dict]:
    """Message[] → Gemini API形式に変換"""
    gemini_history = []
    for msg in messages:
        if msg.role == "system":
            continue  # システムメッセージはスキップ
        role = "model" if msg.role == "assistant" else "user"
        gemini_history.append({
            "role": role,
            "parts": [{"text": msg.content}]
        })
    return gemini_history

@router.post("/agent/query-stream")
async def agent_query_stream(
    request: AgentQueryRequest,
    conv_repo: ConversationRepository = Depends(get_conversation_repository)
):
    conversation_history = None

    # conversation_idがある場合、履歴を取得
    if request.conversation_id:
        conv = await conv_repo.get_conversation(request.conversation_id)
        # Message[] → Gemini形式に変換
        conversation_history = convert_to_gemini_format(conv.messages)

    # ユーザーメッセージを保存
    user_message = Message(
        message_id=str(uuid.uuid4()),
        role="user",
        content=request.query,
        timestamp=datetime.utcnow().isoformat()
    )
    if request.conversation_id:
        await conv_repo.add_message(request.conversation_id, user_message)

    # Orchestratorに履歴を渡す
    final_response_content = ""
    async for event in orchestrator.execute_query_stream(
        user_id=request.user_id,
        query=request.query,
        conversation_history=conversation_history  # ← 追加
    ):
        if event.type == ProgressEventType.FINAL_RESPONSE:
            final_response_content = event.content
        yield f"data: {event.json()}\n\n"

    # アシスタントレスポンスを保存
    if request.conversation_id and final_response_content:
        assistant_message = Message(
            message_id=str(uuid.uuid4()),
            role="assistant",
            content=final_response_content,
            timestamp=datetime.utcnow().isoformat()
        )
        await conv_repo.add_message(request.conversation_id, assistant_message)
```

**やること**:
- 3つの新規エンドポイント追加
- `/agent/query-stream` を更新して履歴取得・保存処理を追加
- Dependency Injection の設定

---

### Phase 5: Frontend - conversationStore作成 (45分)

**ファイル作成**: `frontend/src/store/conversationStore.ts`

```typescript
import { create } from 'zustand'

interface Conversation {
  id: string
  user_id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
}

interface ConversationState {
  currentConversationId: string | null
  conversations: Conversation[]

  createConversation: (userId: string) => Promise<string>
  loadConversation: (id: string) => Promise<void>
  setCurrentConversation: (id: string) => void
  listConversations: (userId: string) => Promise<void>
}

export const useConversationStore = create<ConversationState>((set, get) => ({
  currentConversationId: null,
  conversations: [],

  createConversation: async (userId: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/conversations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId })
    })
    const data = await response.json()
    set({ currentConversationId: data.id })
    return data.id
  },

  loadConversation: async (id: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/conversations/${id}`)
    const conversation = await response.json()
    set({ currentConversationId: id })
    // 必要に応じてメッセージを復元
  },

  setCurrentConversation: (id: string) => {
    set({ currentConversationId: id })
  },

  listConversations: async (userId: string) => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/users/${userId}/conversations`)
    const conversations = await response.json()
    set({ conversations })
  }
}))
```

**やること**:
- Zustand storeを作成
- 会話の作成・取得・一覧取得メソッドを実装
- エラーハンドリング追加

---

### Phase 6: Frontend - useAgentStream更新 (30分)

**ファイル更新**: `frontend/src/hooks/useAgentStream.ts`

```typescript
export const useAgentStream = () => {
  // ... 既存のstate

  const sendQuery = async (
    userId: string,
    query: string,
    conversationId?: string  // ← 追加
  ) => {
    setIsLoading(true)
    setError(null)
    setAgentEvents([])
    setCurrentMessage('')
    setSearchHistory([])

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/agent/query-stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: userId,
          query,
          conversation_id: conversationId  // ← 追加
        })
      })

      // ... 既存のSSE処理
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return { sendQuery, ... }
}
```

**やること**:
- `sendQuery` に `conversationId` パラメータを追加
- APIリクエストに含める

---

### Phase 7: Frontend - ChatPage更新 (45分)

**ファイル更新**: `frontend/src/app/page.tsx`

```typescript
'use client'

import { useState, useEffect } from 'react'
import { useUserStore } from '@/store/userStore'
import { useConversationStore } from '@/store/conversationStore'
import { useAgentStream } from '@/hooks/useAgentStream'
// ... 他のimport

function ChatPage() {
  const selectedUserId = useUserStore((state) => state.selectedUserId)
  const {
    currentConversationId,
    createConversation
  } = useConversationStore()
  const [messages, setMessages] = useState<Message[]>([])
  const { sendQuery, isLoading } = useAgentStream()

  // 初回レンダリング時に新規会話作成
  useEffect(() => {
    if (!currentConversationId && selectedUserId) {
      createConversation(selectedUserId)
    }
  }, [selectedUserId, currentConversationId, createConversation])

  const handleSubmit = async (query: string) => {
    setMessages(prev => [...prev, { role: 'user', content: query }])

    // conversation_idを含めて送信
    await sendQuery(selectedUserId, query, currentConversationId)
  }

  return (
    <div className="flex flex-col h-screen">
      <ChatMessages messages={messages} isLoading={isLoading} />
      <ChatInput onSubmit={handleSubmit} disabled={isLoading} />
    </div>
  )
}

export default function Home() {
  return (
    <MainLayout>
      <ChatPage />
    </MainLayout>
  )
}
```

**やること**:
- 初回レンダリング時に会話を自動作成
- `handleSubmit` で `currentConversationId` を送信
- ユーザー切り替え時の挙動を考慮

---

### Phase 8: Frontend - ConversationList UI作成 (2時間)

**ファイル作成**:
- `frontend/src/components/conversation/ConversationList.tsx`
- `frontend/src/components/conversation/ConversationItem.tsx`

```typescript
// ConversationList.tsx
'use client'

import { useEffect } from 'react'
import { useUserStore } from '@/store/userStore'
import { useConversationStore } from '@/store/conversationStore'
import { ConversationItem } from './ConversationItem'

export function ConversationList() {
  const selectedUserId = useUserStore((state) => state.selectedUserId)
  const {
    conversations,
    currentConversationId,
    listConversations,
    createConversation,
    setCurrentConversation
  } = useConversationStore()

  useEffect(() => {
    if (selectedUserId) {
      listConversations(selectedUserId)
    }
  }, [selectedUserId, listConversations])

  const handleNewConversation = async () => {
    if (selectedUserId) {
      await createConversation(selectedUserId)
    }
  }

  return (
    <div className="w-64 bg-gray-100 h-full overflow-y-auto">
      <div className="p-4">
        <button
          onClick={handleNewConversation}
          className="w-full bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + 新規会話
        </button>
      </div>

      <div className="px-2">
        {conversations.map(conv => (
          <ConversationItem
            key={conv.id}
            conversation={conv}
            isActive={conv.id === currentConversationId}
            onClick={() => setCurrentConversation(conv.id)}
          />
        ))}
      </div>
    </div>
  )
}

// ConversationItem.tsx
interface ConversationItemProps {
  conversation: Conversation
  isActive: boolean
  onClick: () => void
}

export function ConversationItem({ conversation, isActive, onClick }: ConversationItemProps) {
  return (
    <div
      onClick={onClick}
      className={`p-3 mb-2 rounded cursor-pointer ${isActive ? 'bg-blue-100' : 'bg-white hover:bg-gray-50'}`}
    >
      <div className="font-medium text-sm truncate">{conversation.title}</div>
      <div className="text-xs text-gray-500 mt-1">
        {new Date(conversation.updated_at).toLocaleDateString()}
      </div>
    </div>
  )
}
```

**MainLayout更新**: `frontend/src/components/layout/MainLayout.tsx`

```typescript
import { ConversationList } from '@/components/conversation/ConversationList'

export function MainLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <ConversationList />  {/* ← 追加 */}
      <div className="flex-1">{children}</div>
    </div>
  )
}
```

**やること**:
- サイドバーに会話一覧を表示
- 会話切り替え機能
- 新規会話作成ボタン
- アクティブな会話のハイライト

---

### Phase 9: E2Eテスト (1.5時間)

**テストシナリオ**:

1. **新規会話作成テスト**
   - ブラウザでアプリを開く
   - 自動的に新規会話が作成されることを確認
   - DevToolsで `conversation_id` が発行されていることを確認

2. **会話履歴テスト**
   - 「私の担当案件は?」と質問
   - レスポンスを確認
   - 「金額が多い順に並べて」と質問
   - **前の会話を参照してレスポンスが返ること**を確認

3. **会話一覧テスト**
   - サイドバーに会話が表示されることを確認
   - 会話のタイトルが表示されることを確認

4. **会話切り替えテスト**
   - 「+ 新規会話」ボタンをクリック
   - 新しい会話が開始されることを確認
   - 以前の会話を選択
   - 履歴が復元されることを確認

5. **複数ユーザーテスト**
   - ユーザーを切り替え
   - 会話一覧が切り替わることを確認

**確認項目**:
- [ ] 会話履歴が正しくDBに保存されている (Cosmos DB確認)
- [ ] 2回目の質問で前の会話を参照できる
- [ ] 会話一覧が正しく表示される
- [ ] 会話切り替えが動作する
- [ ] ユーザー切り替え時に会話が分離される

**やること**:
- 手動テストで上記シナリオを実施
- バグ修正
- エラーハンドリング改善

---

### Phase 10: オプション機能 - 会話タイトル自動生成 (1時間)

**実装内容**: 最初のユーザーメッセージからタイトルを自動生成

**ファイル更新**: `backend/app/repositories/conversation.py`

```python
async def _generate_title(self, first_query: str) -> str:
    """最初の質問から会話タイトルを生成 (Gemini使用)"""
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        prompt = f"以下の質問を10文字以内で要約してください。質問: {first_query}"

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[{"role": "user", "parts": [{"text": prompt}]}],
            config=types.GenerateContentConfig(temperature=0.3)
        )

        title = response.candidates[0].content.parts[0].text.strip()
        return title[:30]  # 最大30文字
    except Exception as e:
        logger.warning(f"Failed to generate title: {e}")
        # フォールバック: 最初の30文字
        return first_query[:30] + "..." if len(first_query) > 30 else first_query
```

**やること**:
- Gemini APIで会話タイトルを自動生成
- エラー時のフォールバック処理
- UIに反映されることを確認

---

## チェックポイント

| Phase | 確認方法 |
|-------|---------|
| 1-2 | Cosmos DBに `Conversations` コンテナが作成されている |
| 3 | orchestrator.pyが `conversation_history` を受け取れる |
| 4 | Swagger UI (`/docs`) で新規エンドポイントが見える |
| 5-6 | ブラウザDevToolsで `conversation_id` が送信されている |
| 7 | 初回アクセス時に会話IDが自動生成される |
| 8 | サイドバーに会話一覧が表示される |
| 9 | 2回目の質問で前の会話を参照できる |
| 10 | 会話にタイトルが自動付与される |

---

## 技術的考慮事項

### 1. 履歴のトークン制限対策

Gemini APIにはコンテキスト長制限があるため、履歴を切り詰める必要があります。

```python
def truncate_history(
    history: list[dict],
    max_messages: int = 20
) -> list[dict]:
    """最新N件のメッセージのみ保持"""
    if len(history) > max_messages:
        # 最新20件のみ保持
        return history[-max_messages:]
    return history
```

### 2. パフォーマンス最適化

- **Cosmos DB インデックス**: `user_id` + `updated_at` でソート効率化
- **キャッシュ戦略**: Redis等で直近の会話をキャッシュ (オプション)
- **ページネーション**: 会話一覧は50件ずつ取得

### 3. Gemini形式への変換

```python
def convert_to_gemini_format(messages: list[Message]) -> list[dict]:
    """Message[] → Gemini API形式"""
    gemini_history = []
    for msg in messages:
        if msg.role == "system":
            continue  # システムメッセージはスキップ
        role = "model" if msg.role == "assistant" else "user"
        gemini_history.append({
            "role": role,
            "parts": [{"text": msg.content}]
        })
    return gemini_history
```

---

## 簡易版 (3時間で実装)

Phase 1-2-3-4-6-7 のみ実装すれば会話履歴機能は動作します。

**スキップ可能**:
- Phase 5: conversationStore → localStorage で代替
- Phase 8: 会話一覧UI → 最初は不要
- Phase 10: タイトル自動生成 → 最初の30文字で代替

---

## 代替案: ステートレス版 (1-2時間)

**最小実装**:
- DBなし、フロントエンドで履歴管理
- バックエンドAPIに `conversation_history: list[dict]` パラメータ追加のみ
- フロントエンドから毎回全履歴を送信

**メリット**: 実装が最小限
**デメリット**: 履歴の永続化なし、ネットワーク負荷

---

## 工数見積もり

| フェーズ | 時間 |
|---------|------|
| Phase 1-4 (Backend) | 4-6時間 |
| Phase 5-8 (Frontend) | 4-6時間 |
| Phase 9-10 (Testing & Polish) | 2-3時間 |
| **合計** | **10-15時間** |

**簡易版 (ステートレス)**: 1-2時間

---

## 次のステップ

1. このドキュメントをレビュー
2. 実装方式を決定 (ハイブリッド vs 簡易版)
3. Phase 1から順次実装開始
