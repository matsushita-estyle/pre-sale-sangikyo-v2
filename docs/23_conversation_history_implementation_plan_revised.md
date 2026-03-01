# 会話履歴機能 実装計画 (修正版)

**作成日**: 2026-03-01
**対象**: pre-sale-sangikyo-v2
**アーキテクチャ**: ハイブリッド (セッションIDベース)
**見積もり工数**: 10-15時間 (最小構成: 4-5時間)

---

## レビュー結果の反映

### 修正内容
1. **Phase 2**: `update_item()` → `upsert()` に修正 (BaseRepositoryのAPIに合わせる)
2. **Phase 3**: `truncate_history()` の呼び出し場所を明示
3. **Phase 4**: Dependency Injection の実装を詳細化
4. **Phase 4**: メッセージ保存ロジックを明確化

---

## 概要

現在、Agentは各リクエストを独立して処理しており、会話履歴を保持していません。このため、ユーザーが「上記の中で金額が多いのは?」のような前の会話を参照する質問をすると回答できません。

この計画では、**会話ごとにconversation_idを発行し、DBに履歴を保存**する方式で会話履歴機能を実装します。フロントエンドは会話IDだけ送り、バックエンドが履歴を復元してGeminiに渡します。

---

## アーキテクチャ選択

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

**確認方法**:
- Azure Portal で Cosmos DB の `Conversations` コンテナが表示される

---

### Phase 2: ConversationRepository 作成 (1.5時間)

**ファイル作成**: `backend/app/repositories/conversation.py`

```python
import uuid
from datetime import datetime
import logging

from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository):
    """会話履歴のリポジトリ"""

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
        await self.create(conversation.dict())
        logger.info(f"Created conversation {conv_id} for user {user_id}")
        return conversation

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """会話を取得"""
        try:
            # Cosmos DBではidがpartition keyの場合、partition_keyにもidを渡す
            item = await self.get_by_id(conversation_id, conversation_id)
            if item:
                return Conversation(**item)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None

    async def add_message(
        self, conversation_id: str, message: Message
    ) -> Conversation:
        """会話にメッセージ追加"""
        conv = await self.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        conv.messages.append(message)
        conv.updated_at = datetime.utcnow().isoformat()

        # upsertを使用 (BaseRepositoryのAPIに合わせる)
        await self.upsert(conv.dict())
        logger.info(f"Added message to conversation {conversation_id}")
        return conv

    async def list_user_conversations(
        self, user_id: str, limit: int = 50
    ) -> list[Conversation]:
        """ユーザーの会話一覧を取得"""
        query = f"""
            SELECT * FROM c
            WHERE c.user_id = '{user_id}' AND c.is_active = true
            ORDER BY c.updated_at DESC
            OFFSET 0 LIMIT {limit}
        """
        items = await self.query(query)
        return [Conversation(**item) for item in items]

    def _generate_title(self, first_query: str) -> str:
        """最初の質問から会話タイトルを生成 (簡易版)"""
        # Phase 10で Gemini APIを使った自動生成に変更
        return first_query[:30] + "..." if len(first_query) > 30 else first_query
```

**やること**:
- 上記ファイルを作成
- BaseRepositoryのメソッドを使用: `create()`, `get_by_id()`, `upsert()`, `query()`
- エラーハンドリング追加

**確認方法**:
- Python shellで `ConversationRepository()` をインスタンス化できる
- `create_conversation()` を実行してCosmos DBにデータが保存される

---

### Phase 3: Orchestrator更新 (1時間)

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
        # トークン制限対策: 最新20件のみ保持
        chat_history = self._truncate_history(conversation_history, max_messages=20)
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

def _truncate_history(
    self, history: list[dict], max_messages: int = 20
) -> list[dict]:
    """最新N件のメッセージのみ保持 (トークン制限対策)"""
    if len(history) > max_messages:
        logger.info(f"Truncating history from {len(history)} to {max_messages} messages")
        return history[-max_messages:]
    return history
```

**やること**:
- パラメータ `conversation_history` を追加
- 履歴がある場合はそれを使い、新しいクエリを追加
- `_truncate_history()` メソッドを追加してトークン制限対策

**確認方法**:
- orchestratorが `conversation_history=None` で動作する (既存の動作)
- orchestratorが `conversation_history=[...]` で動作する (新機能)

---

### Phase 4: APIスキーマ & エンドポイント更新 (2時間)

#### 4-1: Dependency Injection 設定

**ファイル更新**: `backend/app/api/routes.py` (先頭に追加)

```python
from app.repositories.conversation import ConversationRepository

# Dependency Injection
def get_conversation_repository() -> ConversationRepository:
    """Get conversation repository instance"""
    return ConversationRepository()
```

#### 4-2: スキーマ更新

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

#### 4-3: ヘルパー関数追加

**ファイル更新**: `backend/app/api/routes.py` (エンドポイントの前に追加)

```python
import uuid
from datetime import datetime
from app.models.conversation import Message

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
```

#### 4-4: 新規エンドポイント追加

**ファイル更新**: `backend/app/api/routes.py`

```python
# 会話管理エンドポイント
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    user_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    """新規会話を開始"""
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
    conv = await repo.get_conversation(conversation_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv

@router.get("/users/{user_id}/conversations")
async def list_conversations(
    user_id: str,
    limit: int = Query(50, description="Maximum number of conversations to return"),
    repo: ConversationRepository = Depends(get_conversation_repository)
):
    """会話一覧取得"""
    return await repo.list_user_conversations(user_id, limit)
```

#### 4-5: 既存エンドポイント更新

**ファイル更新**: `backend/app/api/routes.py`

```python
@router.post("/agent/query-stream")
async def agent_query_stream(
    request: AgentQueryRequest,
    conv_repo: ConversationRepository = Depends(get_conversation_repository)
):
    """Agent query with streaming (会話履歴対応版)"""
    conversation_history = None
    final_response_content = ""
    search_history = []

    # conversation_idがある場合、履歴を取得
    if request.conversation_id:
        conv = await conv_repo.get_conversation(request.conversation_id)
        if conv:
            # Message[] → Gemini形式に変換
            conversation_history = convert_to_gemini_format(conv.messages)
        else:
            logger.warning(f"Conversation {request.conversation_id} not found, starting new conversation")

    # ユーザーメッセージを保存
    user_message = Message(
        message_id=str(uuid.uuid4()),
        role="user",
        content=request.query,
        timestamp=datetime.utcnow().isoformat()
    )
    if request.conversation_id:
        try:
            await conv_repo.add_message(request.conversation_id, user_message)
        except ValueError as e:
            logger.error(f"Failed to add user message: {e}")

    # Orchestratorに履歴を渡す
    async def generate_events():
        nonlocal final_response_content, search_history

        async for event in orchestrator.execute_query_stream(
            user_id=request.user_id,
            query=request.query,
            conversation_history=conversation_history  # ← 追加
        ):
            if event.type == ProgressEventType.FINAL_RESPONSE:
                final_response_content = event.content
            elif event.type == ProgressEventType.FUNCTION_CALL:
                search_history.append({
                    "tool_name": event.tool_name,
                    "arguments": event.arguments
                })

            yield f"data: {event.json()}\n\n"

        # アシスタントレスポンスを保存
        if request.conversation_id and final_response_content:
            assistant_message = Message(
                message_id=str(uuid.uuid4()),
                role="assistant",
                content=final_response_content,
                timestamp=datetime.utcnow().isoformat(),
                search_history=search_history if search_history else None
            )
            try:
                await conv_repo.add_message(request.conversation_id, assistant_message)
            except Exception as e:
                logger.error(f"Failed to add assistant message: {e}")

    return StreamingResponse(generate_events(), media_type="text/event-stream")
```

**やること**:
- Dependency Injection 関数を追加
- 3つの新規エンドポイント追加
- `/agent/query-stream` を更新して履歴取得・保存処理を追加
- メッセージ保存ロジックを明確化 (ユーザーメッセージ → Agent実行 → アシスタントメッセージ)

**確認方法**:
- Swagger UI (`http://localhost:8000/docs`) で新規エンドポイントが表示される
- `/conversations` (POST) で会話が作成できる
- `/agent/query-stream` で `conversation_id` を送信できる

---

### Phase 5-10: Frontend実装

*(前のドキュメントと同じ内容のため省略)*

---

## 修正点のまとめ

| 修正箇所 | 変更前 | 変更後 | 理由 |
|---------|--------|--------|------|
| Phase 2 | `update_item()` | `upsert()` | BaseRepositoryのAPIに存在しない |
| Phase 3 | トークン制限対策が未実装 | `_truncate_history()` 追加 | 実装場所を明確化 |
| Phase 4 | `get_conversation_repository` が未定義 | Dependency Injection 関数を追加 | 実装方法を明確化 |
| Phase 4 | メッセージ保存が曖昧 | 詳細なロジックを記載 | ユーザー/アシスタント両方のメッセージ保存 |

---

## 最小構成 (4-5時間で実装)

Phase 1-2-3-4 のみ実装すれば会話履歴機能は動作します。

**実装内容**:
- データモデル作成
- ConversationRepository 作成
- Orchestrator更新
- API更新

**スキップ可能**:
- Phase 5-8: Frontend (後で実装)
- Phase 10: タイトル自動生成 (簡易版を使用)

**テスト方法**:
1. Swagger UIで `/conversations` (POST) を実行 → conversation_id取得
2. `/agent/query-stream` で `conversation_id` を含めて質問1を送信
3. `/agent/query-stream` で同じ `conversation_id` で質問2を送信 → 履歴が参照される

---

## 次のステップ

1. このドキュメントをレビュー
2. Phase 1から順次実装開始
3. 各Phaseの確認方法でテスト
