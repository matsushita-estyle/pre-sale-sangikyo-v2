# Gemini Function Calling Agent 設計ドキュメント

**作成日**: 2026-03-01
**目的**: MockAgentOrchestratorから実際のGemini Function Calling Agentへの移行

## 1. 概要

### 1.1 背景
現在、エージェントの進捗通信システムは`MockAgentOrchestrator`を使用して検証済み。次のステップとして、実際のGemini Function Calling APIを使用したエージェントを実装する。

### 1.2 目標
- Gemini 2.0 Flash Expを使用したFunction Calling Agent
- 6つのツール関数によるCosmosDBデータアクセス
- SSEストリーミングでリアルタイム進捗通知
- 既存のフロントエンド（検索履歴機能含む）をそのまま利用

### 1.3 アーキテクチャ

```
User Query
    ↓
Frontend (useAgentStream)
    ↓
Backend SSE Endpoint (/api/v1/agent/query-stream)
    ↓
AgentOrchestrator
    ├─ Gemini 2.0 Flash Exp (Function Calling)
    ├─ System Prompt
    └─ Tools (6 functions)
        ├─ get_user_info → UserRepository
        ├─ search_customers → CustomerRepository
        ├─ get_customer_details → CustomerRepository
        ├─ search_deals → DealRepository
        ├─ get_deal_details → DealRepository
        └─ search_latest_news → (Mock/External API)
    ↓
ProgressEvent Stream (SSE)
    ↓
Frontend (進捗表示 + 検索履歴)
```

## 2. ツール定義

### 2.1 ツール一覧

| ツール名 | 説明 | 入力パラメータ | 出力 | データソース |
|---------|------|---------------|------|-------------|
| `get_user_info` | ユーザー情報取得 | `user_id: str` | User情報 | UserRepository |
| `search_customers` | 顧客検索 | `industries?: list[str]`<br>`keyword?: str` | Customer一覧 | CustomerRepository |
| `get_customer_details` | 顧客詳細取得 | `customer_id: str` | Customer詳細 | CustomerRepository |
| `search_deals` | 案件検索 | `sales_user_id?: str`<br>`deal_stage?: str`<br>`customer_id?: str` | Deal一覧 | DealRepository |
| `get_deal_details` | 案件詳細取得 | `deal_id: str` | Deal詳細 | DealRepository |
| `search_latest_news` | 最新ニュース検索 | `keywords: list[str]`<br>`days?: int` | ニュース一覧 | Mock/External API |

### 2.2 ツール詳細設計

#### 2.2.1 get_user_info

**目的**: 指定されたユーザーIDのユーザー情報を取得

**Gemini Function Declaration**:
```python
{
    "name": "get_user_info",
    "description": "指定されたユーザーIDのユーザー情報（名前、メールアドレス、部署、役職）を取得します。",
    "parameters": {
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "ユーザーID（例: 1, 2, 3）"
            }
        },
        "required": ["user_id"]
    }
}
```

**実装**:
```python
async def get_user_info(user_id: str) -> str:
    """Get user information."""
    repo = UserRepository()
    user = await repo.get_user_by_id(user_id)

    if not user:
        return f"ユーザーID {user_id} は見つかりませんでした。"

    return f"""ユーザー情報:
- 名前: {user.name}
- メール: {user.email}
- 部署: {user.department or 'なし'}
- 役職: {user.role or 'なし'}"""
```

#### 2.2.2 search_customers

**目的**: 業界やキーワードで顧客を検索

**Gemini Function Declaration**:
```python
{
    "name": "search_customers",
    "description": "業界やキーワードで顧客を検索します。複数の条件を指定可能です。",
    "parameters": {
        "type": "object",
        "properties": {
            "industries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "業界のリスト（例: ['IT', '通信', '製造']）。指定した業界のいずれかに該当する顧客を検索します。"
            },
            "keyword": {
                "type": "string",
                "description": "顧客名に含まれるキーワード（部分一致）"
            }
        },
        "required": []
    }
}
```

**実装**:
```python
async def search_customers(
    industries: list[str] | None = None,
    keyword: str | None = None
) -> str:
    """Search customers by industries or keyword."""
    repo = CustomerRepository()
    customers = []

    # 業界で検索
    if industries:
        for industry in industries:
            industry_customers = await repo.get_customers_by_industry(industry)
            customers.extend(industry_customers)

    # キーワードで検索
    if keyword:
        keyword_customers = await repo.search_customers(keyword)
        customers.extend(keyword_customers)

    # 条件がない場合は全件取得
    if not industries and not keyword:
        customers = await repo.get_all_customers()

    # 重複除去
    unique_customers = {c.customer_id: c for c in customers}.values()

    if not unique_customers:
        return "該当する顧客が見つかりませんでした。"

    result = f"{len(unique_customers)}件の顧客が見つかりました:\n\n"
    for customer in unique_customers:
        result += f"- {customer.name} (ID: {customer.customer_id})\n"
        result += f"  業界: {customer.industry or 'なし'}\n"
        result += f"  担当者: {customer.contact_person or 'なし'}\n\n"

    return result
```

#### 2.2.3 get_customer_details

**目的**: 顧客IDから顧客の詳細情報を取得

**Gemini Function Declaration**:
```python
{
    "name": "get_customer_details",
    "description": "指定された顧客IDの詳細情報を取得します。",
    "parameters": {
        "type": "object",
        "properties": {
            "customer_id": {
                "type": "string",
                "description": "顧客ID"
            }
        },
        "required": ["customer_id"]
    }
}
```

**実装**:
```python
async def get_customer_details(customer_id: str) -> str:
    """Get customer details."""
    repo = CustomerRepository()
    customer = await repo.get_customer_by_id(customer_id)

    if not customer:
        return f"顧客ID {customer_id} は見つかりませんでした。"

    return f"""顧客詳細:
- 顧客名: {customer.name}
- 業界: {customer.industry or 'なし'}
- 担当者: {customer.contact_person or 'なし'}
- メール: {customer.email or 'なし'}
- 電話番号: {customer.phone or 'なし'}"""
```

#### 2.2.4 search_deals

**目的**: 営業担当者、案件ステージ、顧客IDで案件を検索

**Gemini Function Declaration**:
```python
{
    "name": "search_deals",
    "description": "営業担当者、案件ステージ、顧客IDで案件を検索します。",
    "parameters": {
        "type": "object",
        "properties": {
            "sales_user_id": {
                "type": "string",
                "description": "営業担当者のユーザーID"
            },
            "deal_stage": {
                "type": "string",
                "description": "案件ステージ（見込み、提案、商談、受注、失注）",
                "enum": ["見込み", "提案", "商談", "受注", "失注"]
            },
            "customer_id": {
                "type": "string",
                "description": "顧客ID"
            }
        },
        "required": []
    }
}
```

**実装**:
```python
async def search_deals(
    sales_user_id: str | None = None,
    deal_stage: str | None = None,
    customer_id: str | None = None
) -> str:
    """Search deals by sales user, stage, or customer."""
    repo = DealRepository()
    deals = []

    # 営業担当者で検索
    if sales_user_id:
        deals = await repo.get_deals_by_user(sales_user_id)

    # 顧客で検索
    elif customer_id:
        deals = await repo.get_deals_by_customer(customer_id)

    # ステージで検索
    elif deal_stage:
        deals = await repo.get_deals_by_stage(deal_stage)

    # 条件がない場合は全件取得
    else:
        deals = await repo.get_all_deals()

    # フィルタリング（複数条件が指定された場合）
    if sales_user_id and deals:
        deals = [d for d in deals if d.sales_user_id == sales_user_id]
    if deal_stage and deals:
        deals = [d for d in deals if d.deal_stage == deal_stage]
    if customer_id and deals:
        deals = [d for d in deals if d.customer_id == customer_id]

    if not deals:
        return "該当する案件が見つかりませんでした。"

    result = f"{len(deals)}件の案件が見つかりました:\n\n"
    for deal in deals:
        result += f"- 案件ID: {deal.deal_id}\n"
        result += f"  顧客: {deal.customer_name or 'なし'}\n"
        result += f"  ステージ: {deal.deal_stage}\n"
        result += f"  金額: {deal.deal_amount}円\n"
        result += f"  サービス: {deal.service_type or 'なし'}\n\n"

    return result
```

#### 2.2.5 get_deal_details

**目的**: 案件IDから案件の詳細情報を取得

**Gemini Function Declaration**:
```python
{
    "name": "get_deal_details",
    "description": "指定された案件IDの詳細情報を取得します。",
    "parameters": {
        "type": "object",
        "properties": {
            "deal_id": {
                "type": "string",
                "description": "案件ID"
            }
        },
        "required": ["deal_id"]
    }
}
```

**実装**:
```python
async def get_deal_details(deal_id: str) -> str:
    """Get deal details."""
    repo = DealRepository()
    deal = await repo.get_deal_by_id(deal_id)

    if not deal:
        return f"案件ID {deal_id} は見つかりませんでした。"

    return f"""案件詳細:
- 案件ID: {deal.deal_id}
- 顧客: {deal.customer_name or 'なし'}
- 営業担当: {deal.sales_user_name or 'なし'}
- ステージ: {deal.deal_stage}
- 金額: {deal.deal_amount}円
- サービス種別: {deal.service_type or 'なし'}
- 最終接触日: {deal.last_contact_date or 'なし'}
- メモ: {deal.notes or 'なし'}"""
```

#### 2.2.6 search_latest_news

**目的**: キーワードで最新ニュースを検索（モックまたは外部API）

**Gemini Function Declaration**:
```python
{
    "name": "search_latest_news",
    "description": "指定されたキーワードで最新のニュースを検索します。",
    "parameters": {
        "type": "object",
        "properties": {
            "keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "検索キーワードのリスト（例: ['KDDI', '5G']）"
            },
            "days": {
                "type": "integer",
                "description": "過去何日分のニュースを検索するか（デフォルト: 7日）",
                "default": 7
            }
        },
        "required": ["keywords"]
    }
}
```

**実装（モック版）**:
```python
async def search_latest_news(keywords: list[str], days: int = 7) -> str:
    """Search latest news (mock implementation)."""
    # TODO: 実際のニュースAPIに置き換える
    keyword_str = "、".join(keywords)

    mock_news = [
        {
            "title": f"{keywords[0]}、次世代通信インフラに1000億円投資",
            "date": "2026-02-28",
            "summary": f"{keywords[0]}は次世代通信インフラの構築に向けて、総額1000億円の投資を発表しました。"
        },
        {
            "title": f"{keywords[0]}、AI活用の新サービス開始",
            "date": "2026-02-27",
            "summary": f"{keywords[0]}はAI技術を活用した新しいサービスを3月から開始すると発表しました。"
        },
    ]

    result = f"{keyword_str} に関する最新ニュース（過去{days}日間）:\n\n"
    for news in mock_news:
        result += f"- {news['title']}\n"
        result += f"  日付: {news['date']}\n"
        result += f"  概要: {news['summary']}\n\n"

    return result
```

## 3. AgentOrchestrator 実装設計

### 3.1 クラス構造

```python
# backend/app/agent/orchestrator.py

import logging
from typing import AsyncIterator

from google import genai
from google.genai import types

from app.schemas.agent import ProgressEvent, ProgressEventType
from app.agent.tools import get_tools, execute_tool

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Gemini Function Calling Agent Orchestrator."""

    def __init__(self):
        """Initialize agent with Gemini model."""
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self.model_id = "gemini-2.0-flash"
        self.tools = get_tools()
        self.system_instruction = self._get_system_instruction()

    def _get_system_instruction(self) -> str:
        """Get system instruction for the agent."""
        return """あなたは営業支援AIアシスタントです。
営業担当者の案件管理、顧客情報検索、最新ニュース収集をサポートします。

利用可能なツール:
- get_user_info: ユーザー情報を取得
- search_customers: 顧客を検索
- get_customer_details: 顧客詳細を取得
- search_deals: 案件を検索
- get_deal_details: 案件詳細を取得
- search_latest_news: 最新ニュースを検索

回答時のガイドライン:
1. 必要なツールを適切に使用して情報を収集する
2. 簡潔で分かりやすい回答を心がける
3. Markdown形式で構造化された回答を返す
4. 数値やデータは正確に伝える
5. ユーザーの質問に直接答える
"""

    async def execute_query_stream(
        self, user_id: str, query: str
    ) -> AsyncIterator[ProgressEvent]:
        """Execute query with function calling and stream progress."""

        # 初期メッセージ
        yield ProgressEvent(
            type=ProgressEventType.THINKING,
            message="クエリを解析中..."
        )

        # チャット履歴の初期化
        chat_history = [{"role": "user", "parts": [{"text": query}]}]

        # Function Calling ループ
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Geminiにリクエスト送信
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=chat_history,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    tools=self.tools,
                    temperature=0.7,
                )
            )

            # レスポンスの解析
            if not response.candidates:
                yield ProgressEvent(
                    type=ProgressEventType.ERROR,
                    message="レスポンスを生成できませんでした。"
                )
                return

            candidate = response.candidates[0]

            # Function Call があるか確認
            if candidate.content.parts and any(
                hasattr(part, "function_call") for part in candidate.content.parts
            ):
                # Function Call を実行
                function_responses = []

                for part in candidate.content.parts:
                    if hasattr(part, "function_call"):
                        fc = part.function_call

                        # Function Call イベントを送信
                        yield ProgressEvent(
                            type=ProgressEventType.FUNCTION_CALL,
                            tool_name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                            message=f"{fc.name}を実行中..."
                        )

                        # ツールを実行
                        try:
                            result = await execute_tool(fc.name, dict(fc.args) if fc.args else {})

                            # Function Result イベントを送信
                            yield ProgressEvent(
                                type=ProgressEventType.FUNCTION_RESULT,
                                tool_name=fc.name,
                                result=f"{fc.name}の実行が完了しました"
                            )

                            # Function Response を作成
                            function_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={"result": result}
                                )
                            )

                        except Exception as e:
                            logger.error(f"Error executing tool {fc.name}: {e}", exc_info=True)
                            yield ProgressEvent(
                                type=ProgressEventType.ERROR,
                                message=f"{fc.name}の実行中にエラーが発生しました: {str(e)}"
                            )
                            return

                # チャット履歴にFunction Callとその結果を追加
                chat_history.append({"role": "model", "parts": candidate.content.parts})
                chat_history.append({"role": "user", "parts": function_responses})

            else:
                # テキストレスポンスがある場合は終了
                if candidate.content.parts:
                    text_parts = [part.text for part in candidate.content.parts if hasattr(part, "text")]
                    if text_parts:
                        final_response = "".join(text_parts)

                        yield ProgressEvent(
                            type=ProgressEventType.FINAL_RESPONSE,
                            content=final_response
                        )
                        return

                # それ以外の場合はエラー
                yield ProgressEvent(
                    type=ProgressEventType.ERROR,
                    message="予期しないレスポンス形式です。"
                )
                return

        # 最大反復回数に達した場合
        yield ProgressEvent(
            type=ProgressEventType.ERROR,
            message="最大反復回数に達しました。"
        )
```

### 3.2 ツール実装ファイル

```python
# backend/app/agent/tools.py

import os
from typing import Any

from google.genai import types

from app.repositories.user import UserRepository
from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository

# ツール関数の実装（上記2.2節を参照）
async def get_user_info(user_id: str) -> str:
    # ... 実装 ...
    pass

async def search_customers(industries: list[str] | None = None, keyword: str | None = None) -> str:
    # ... 実装 ...
    pass

# ... 他のツール関数 ...

def get_tools() -> list[types.Tool]:
    """Get Gemini tool declarations."""
    return [
        types.Tool(
            function_declarations=[
                types.FunctionDeclaration(
                    name="get_user_info",
                    description="指定されたユーザーIDのユーザー情報（名前、メールアドレス、部署、役職）を取得します。",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "user_id": types.Schema(
                                type=types.Type.STRING,
                                description="ユーザーID（例: 1, 2, 3）"
                            )
                        },
                        required=["user_id"]
                    )
                ),
                types.FunctionDeclaration(
                    name="search_customers",
                    description="業界やキーワードで顧客を検索します。複数の条件を指定可能です。",
                    parameters=types.Schema(
                        type=types.Type.OBJECT,
                        properties={
                            "industries": types.Schema(
                                type=types.Type.ARRAY,
                                items=types.Schema(type=types.Type.STRING),
                                description="業界のリスト（例: ['IT', '通信', '製造']）"
                            ),
                            "keyword": types.Schema(
                                type=types.Type.STRING,
                                description="顧客名に含まれるキーワード（部分一致）"
                            )
                        }
                    )
                ),
                # ... 他のツール定義 ...
            ]
        )
    ]

async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name."""
    if tool_name == "get_user_info":
        return await get_user_info(**arguments)
    elif tool_name == "search_customers":
        return await search_customers(**arguments)
    elif tool_name == "get_customer_details":
        return await get_customer_details(**arguments)
    elif tool_name == "search_deals":
        return await search_deals(**arguments)
    elif tool_name == "get_deal_details":
        return await get_deal_details(**arguments)
    elif tool_name == "search_latest_news":
        return await search_latest_news(**arguments)
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
```

## 4. エンドポイント統合

### 4.1 routes.py の修正

```python
# backend/app/api/routes.py

# Before:
# from app.agent.mock_orchestrator import MockAgentOrchestrator

# After:
from app.agent.orchestrator import AgentOrchestrator

@router.post("/agent/query-stream")
async def agent_query_stream(request: AgentQueryRequest):
    """エージェントクエリ（SSEストリーミング）"""

    # MockAgentOrchestrator → AgentOrchestrator に変更
    orchestrator = AgentOrchestrator()

    async def generate():
        try:
            async for event in orchestrator.execute_query_stream(
                request.user_id, request.query
            ):
                yield f"data: {event.model_dump_json()}\n\n"
        except Exception as e:
            logger.error(f"Error in agent query stream: {e}", exc_info=True)
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
            "X-Accel-Buffering": "no",
        },
    )
```

## 5. 実装手順

### Phase 1: ツール実装（2-3時間）

1. `backend/app/agent/tools.py` 作成
   - 6つのツール関数実装
   - `get_tools()` 関数でGemini用の宣言を返す
   - `execute_tool()` ディスパッチャー実装

2. ユニットテストの作成（オプション）
   - 各ツール関数が正しく動作するかテスト

### Phase 2: Agent実装（3-4時間）

1. `backend/app/agent/orchestrator.py` 作成
   - `AgentOrchestrator` クラス実装
   - Function Callingループ
   - ProgressEventストリーミング

2. エラーハンドリング
   - ツール実行失敗時の処理
   - Gemini APIエラーの処理
   - タイムアウト処理

### Phase 3: プロンプト調整（1時間）

1. システムプロンプトの最適化
   - ペルソナ設定
   - ツール使用のガイドライン
   - 回答形式の指定

2. テストクエリでの検証
   - 適切なツールが呼ばれるか
   - 回答の品質確認

### Phase 4: 統合（30分）

1. `routes.py` の修正
   - `MockAgentOrchestrator` → `AgentOrchestrator`

2. 環境変数確認
   - `GEMINI_API_KEY` が設定されているか

### Phase 5: テスト（2時間）

1. 単体テスト
   - 各ツール関数のテスト
   - AgentOrchestratorの基本動作テスト

2. 統合テスト
   - curlでSSEエンドポイントをテスト
   - 複数ターンのFunction Callingが動作するか

3. E2Eテスト
   - ブラウザからのテスト
   - 進捗表示の確認
   - 検索履歴の確認

## 6. テストシナリオ

### 6.1 基本シナリオ

**クエリ**: 「私の担当案件を教えて」

**期待される動作**:
1. `get_user_info(user_id="1")` → ユーザー情報取得
2. `search_deals(sales_user_id="1")` → 担当案件一覧取得
3. 最終レスポンス: Markdown形式で案件一覧を返す

**検証ポイント**:
- ProgressEventが正しく送信されるか
- 検索履歴に2件（get_user_info, search_deals）が記録されるか
- 最終レスポンスがMarkdown形式か

### 6.2 複雑シナリオ

**クエリ**: 「IT業界の顧客に対する進行中の案件と、KDDIの最新ニュースを教えて」

**期待される動作**:
1. `search_customers(industries=["IT"])` → IT業界の顧客検索
2. `search_deals(deal_stage="商談")` → 進行中の案件検索
3. `search_latest_news(keywords=["KDDI"])` → KDDIのニュース検索
4. 最終レスポンス: 3つの情報を統合したレポート

### 6.3 エラーハンドリングシナリオ

**クエリ**: 「存在しない顧客ID '999' の詳細を教えて」

**期待される動作**:
1. `get_customer_details(customer_id="999")` → エラーメッセージを返す
2. 最終レスポンス: 「顧客ID 999 は見つかりませんでした」

## 7. パフォーマンスとコスト考慮

### 7.1 レスポンス時間

- 単純なクエリ: 2-3秒
- 複数ツール呼び出し: 5-10秒
- 最大反復回数: 10回（最悪ケース: 30秒）

### 7.2 Gemini APIコスト

- モデル: gemini-2.0-flash
- 入力トークン: 約$0.15 / 1M tokens
- 出力トークン: 約$0.6 / 1M tokens

**推定コスト**（1クエリあたり）:
- 入力: 500 tokens × $0.15 / 1M = $0.000075
- 出力: 200 tokens × $0.6 / 1M = $0.00012
- 合計: **約$0.0002 (0.02円)**

### 7.3 最適化案

1. **キャッシング**: 同じツール呼び出しの結果をキャッシュ
2. **並列実行**: 独立したツール呼び出しを並列化
3. **早期終了**: 十分な情報が集まったら早期に回答生成

## 8. 今後の拡張

1. **会話履歴の保持**
   - 複数ターンの会話をサポート
   - コンテキストを維持

2. **ツールの追加**
   - メール送信
   - カレンダー連携
   - レポート生成

3. **外部API連携**
   - 実際のニュースAPI
   - 天気予報
   - 株価情報

4. **マルチモーダル**
   - 画像の解析
   - グラフの生成
   - PDFレポート作成

## 9. セキュリティ考慮事項

1. **入力検証**
   - ツール引数のバリデーション
   - SQLインジェクション対策（Cosmos DBクエリ）

2. **認証・認可**
   - ユーザーIDの検証
   - 他のユーザーのデータにアクセスできないようにする

3. **レート制限**
   - Gemini APIの呼び出し回数制限
   - DDoS対策

4. **ログとモニタリング**
   - すべてのツール呼び出しをログ
   - エラー率のモニタリング

## 10. まとめ

この設計ドキュメントに従って実装することで:

✅ Gemini Function Calling Agentの本格実装
✅ 既存のリポジトリ層を活用したデータアクセス
✅ リアルタイム進捗通知とSSEストリーミング
✅ フロントエンドの変更なし（検索履歴機能もそのまま利用可能）

次のステップ: Phase 1のツール実装から開始することを推奨。
