# 今後の開発計画

**日付:** 2026-03-01
**概要:** pre-sale-sangikyo-v2の次期開発ステップと優先順位
**参照:** docs/07_backend_migration_plan.md

---

## 1. 全体方針

### 1.1 現在の状態
- ✅ フロントエンド実装完了（Next.js + Tailwind CSS）
- ✅ バックエンドAPI実装完了（FastAPI + Cosmos DB）
- ✅ 基本的なAIチャット機能実装（Gemini API - シンプルなプロンプトベース）
- ✅ Markdownレンダリング改善
- ✅ コード品質向上（Ruff導入）
- ✅ プロンプト管理改善
- ✅ Azureデプロイ完了

### 1.2 現在の制限事項と課題
- ❌ **Gemini Function Calling未実装**（sample-sales-agent-demoの核心機能）
- ❌ エージェントツール未実装（顧客検索、製品検索、ニュース検索）
- ❌ エージェントオーケストレーター未実装
- ❌ ストリーミングレスポンス（SSE）未対応
- ❌ テストが未実装
- ❌ CI/CDパイプラインがない
- ❌ エラーハンドリングが不十分

### 1.3 方針
- **認証機能は不要**（デモアプリのため、user_id=1でハードコード）
- **07_backend_migration_plan.mdに従って段階的に実装**
- sample-sales-agent-demoのエージェント機能を移植することが最優先

---

## 2. 優先度別タスク

### 優先度: 最高 🔴🔴（必須機能 - 07のプラン実行）

#### 2.1 エージェント機能の実装（Gemini Function Calling）

**目的:** sample-sales-agent-demoの主要機能を移植し、AIエージェントとして機能させる

**背景:**
現在のチャット機能はシンプルなプロンプトベースで、Cosmos DBのデータを文字列として渡しているのみ。
sample-sales-agent-demoは、Function Calling + ツール群でデータを動的に取得・活用する高度なエージェント。

**フェーズ3: エージェントツールの実装（docs/07参照）**

**タスク3-1: 最もシンプルなツールの実装**
- `backend/app/agent/tools.py` を作成
- `get_user_attributes` ツールを実装
  - ユーザーの担当業界・地域を取得
  - Gemini Function Declaration の定義
  - Cosmos DBからのデータ取得ロジック

**タスク3-2: 残りのツールの実装**
- `search_customers`: 顧客検索（業界、地域でフィルタ）
- `search_products`: 製品検索（カテゴリでフィルタ）
- `search_latest_news`: ニュース検索（キーワードベース）

**期待される成果:**
```python
# ツールが個別に動作することを確認
from app.agent.tools import get_user_attributes, search_customers

result1 = get_user_attributes(db, user_id=1)
# → {'担当業界': ['IT', '通信'], '担当地域': ['西日本']}

result2 = search_customers(db, industries=["IT"])
# → [顧客リスト]
```

**工数見積もり:** 1-2日

---

**フェーズ4: エージェントオーケストレーターの実装（docs/07参照）**

**タスク4-1: システムプロンプトの設定**
- `backend/app/agent/prompts.py` を作成（または既存のapp/prompts/を拡張）
- sample-sales-agent-demoのシステムプロンプトを移植
- 営業レポート形式の指定

**タスク4-2: オーケストレーターの実装（基本版）**
- `backend/app/agent/orchestrator.py` を作成
- Gemini API の `generate_content` を使用
- Function Calling ループの実装:
  1. ユーザークエリを送信
  2. Geminiがツール呼び出しを返す
  3. ツールを実行して結果を取得
  4. 結果をGeminiに返す
  5. 最終回答が返るまで繰り返し（最大10イテレーション）

**タスク4-3: SSEストリーミング対応**
- `on_step` コールバックの実装
- 各ステップの進捗をリアルタイム送信
  - 「顧客を検索中...」
  - 「ニュースを取得中...」
  - 「レポートを作成中...」

**期待される成果:**
```python
# コンソールでエージェントが動作することを確認
agent = SalesAgentOrchestrator(api_key="...")
result = await agent.execute_query(user_id=1, query="担当企業について教えて")
# → ツールが自動で呼び出され、営業レポートが返る
```

**工数見積もり:** 2-3日

---

**フェーズ5: APIエンドポイントの統合（docs/07参照）**

**タスク5-1: 通常の問い合わせエンドポイント**
- `POST /api/v1/sales-agent/query` を実装
- 既存の `/api/v1/copilot/chat` を置き換えまたは並行運用

**タスク5-2: SSEストリーミングエンドポイント**
- `POST /api/v1/sales-agent/query-stream` を実装
- FastAPI の `StreamingResponse` を使用
- フロントエンドにリアルタイムで進捗を送信

**タスク5-3: フロントエンドとの接続**
- フロントエンドでEventSourceを使用してSSE受信
- 進捗表示UI（「顧客を検索中...」等）
- ストリーミング中のローディング表示

**期待される成果:**
```bash
# curlでテスト
curl -X POST http://localhost:8000/api/v1/sales-agent/query \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "query": "担当企業を教えて"}'

# SSEストリーミングでテスト
curl -N -X POST http://localhost:8000/api/v1/sales-agent/query-stream \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "query": "担当企業を教えて"}'
```

**工数見積もり:** 1-2日

---

**エージェント機能実装の合計工数:** 4-7日

---

### 優先度: 高 🔴

#### 2.2 エラーハンドリングの強化
**目的:** ユーザー体験の向上とデバッグの効率化

**実装タスク:**

**バックエンド:**
- カスタムエラークラスの拡充
  ```python
  class GeminiAPIError(AppException):
      """Gemini API関連のエラー"""
      pass

  class QuotaExceededError(GeminiAPIError):
      """APIクォータ超過エラー"""
      pass
  ```
- リトライロジックの実装
  ```python
  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(
      stop=stop_after_attempt(3),
      wait=wait_exponential(multiplier=1, min=4, max=10)
  )
  async def call_gemini_api(prompt: str):
      # ...
  ```

**フロントエンド:**
- エラー種別ごとの表示改善
- ユーザーフレンドリーなエラーメッセージ

**工数見積もり:** 1-2日

---

#### 2.3 テストの追加
**目的:** コードの品質保証とリファクタリングの安全性確保

**バックエンド（pytest）:**
```python
# tests/test_agent_tools.py
@pytest.mark.asyncio
async def test_get_user_attributes():
    result = get_user_attributes(db, user_id=1)
    assert "担当業界" in result

# tests/test_orchestrator.py
@pytest.mark.asyncio
async def test_agent_executes_query():
    agent = SalesAgentOrchestrator()
    response = await agent.execute_query(user_id=1, query="担当案件を教えて")
    assert response is not None
```

**フロントエンド（Jest + React Testing Library）:**
```typescript
// __tests__/ChatMessage.test.tsx
describe('ChatMessage', () => {
  it('renders markdown headings correctly', () => {
    render(<ChatMessage role="assistant" content="## テスト見出し" />)
    expect(screen.getByText('テスト見出し')).toBeInTheDocument()
  })
})
```

**工数見積もり:** 3-4日

---

### 優先度: 中 🟡

#### 2.4 CI/CDパイプラインの構築
**目的:** 自動テスト・デプロイによる開発効率化

**GitHub Actions:**
- バックエンドCI（Ruff + pytest）
- フロントエンドCI（ESLint + Jest + Build）
- Azure自動デプロイ

**工数見積もり:** 2-3日

---

#### 2.5 ロギング・モニタリングの強化
**目的:** 本番環境での問題発見と分析

**Azure Application Insights統合:**
- カスタムイベント・メトリクスの追加
- エラートラッキング
- パフォーマンスモニタリング

**工数見積もり:** 2日

---

### 優先度: 低 🟢

#### 2.6 UI/UX改善
- ダークモード対応
- レスポンシブデザイン改善
- アクセシビリティ向上

**工数見積もり:** 3-4日

---

#### 2.7 パフォーマンス最適化
- フロントエンド: コード分割、画像最適化
- バックエンド: Cosmos DBクエリ最適化、キャッシング

**工数見積もり:** 2-3日

---

#### 2.8 国際化（i18n）
- next-intl導入
- 日本語/英語対応

**工数見積もり:** 2-3日

---

## 3. 推奨実装順序

### フェーズ1: エージェント機能実装（1-2週間）🔴🔴
1. ✅ **エージェントツールの実装**（1-2日）
   - get_user_attributes
   - search_customers
   - search_products
   - search_latest_news

2. ✅ **オーケストレーターの実装**（2-3日）
   - システムプロンプト
   - Function Callingループ
   - SSEストリーミング対応

3. ✅ **APIエンドポイントの統合**（1-2日）
   - /sales-agent/query
   - /sales-agent/query-stream
   - フロントエンド接続

### フェーズ2: 品質向上（1週間）🔴
4. ✅ **エラーハンドリングの強化**（1-2日）
5. ✅ **テストの追加**（3-4日）

### フェーズ3: 運用基盤（1週間）🟡
6. ⭕ **CI/CDパイプラインの構築**（2-3日）
7. ⭕ **ロギング・モニタリングの強化**（2日）

### フェーズ4: 追加機能（1-2週間）🟢
8. ⭕ **UI/UX改善**（3-4日）
9. ⭕ **パフォーマンス最適化**（2-3日）
10. ⭕ **国際化**（2-3日）

---

## 4. 技術的な検討事項

### 4.1 Gemini Function Calling
- **ツール定義:** `types.FunctionDeclaration` を使用
- **パラメータスキーマ:** JSONSchemaでパラメータを定義
- **ループ制御:** 最大10イテレーション、無限ループ防止

### 4.2 SSE（Server-Sent Events）
- **FastAPI:** `StreamingResponse` + async generator
- **フロントエンド:** `EventSource` API
- **フォーマット:** `data: {json}\n\n`

### 4.3 テストカバレッジ目標
- バックエンド: 70%以上（エージェントロジック: 80%以上）
- フロントエンド: 60%以上
- 重要なビジネスロジック: 90%以上

---

## 5. リスクと対策

### 5.1 Gemini API制限
**リスク:** 無料枠のクォータ超過

**対策:**
- リトライロジックの実装
- エラーハンドリング強化
- 必要に応じて有料プランへの移行

### 5.2 Cosmos DB コスト
**リスク:** データ量増加によるコスト増

**対策:**
- RU（Request Unit）の最適化
- 不要なインデックス削除
- パーティション戦略の見直し

### 5.3 Function Calling実装の複雑さ
**リスク:** エージェントループのデバッグが困難

**対策:**
- 詳細なロギング追加
- 各ステップの進捗を可視化
- ユニットテストで個別ツールを検証

---

## 6. まとめ

### 6.1 最優先タスク（次の1-2週間で実施）
1. **エージェントツールの実装** - Function Callingの基盤
2. **オーケストレーターの実装** - エージェントのコアロジック
3. **APIエンドポイントの統合** - フロントエンドとの接続
4. **SSEストリーミング** - リアルタイムUX

### 6.2 中期目標（3-4週間後）
5. **エラーハンドリング強化** - 安定性向上
6. **テストの追加** - 品質保証
7. **CI/CD構築** - 開発効率化

### 6.3 長期目標（1-2ヶ月後）
8. **モニタリング強化** - 運用品質
9. **UI/UX改善** - ユーザー満足度
10. **パフォーマンス最適化** - スケーラビリティ

---

## 7. 次のアクション

**即座に着手すべきタスク:**
1. `backend/app/agent/tools.py` の作成とツール実装
2. `backend/app/agent/orchestrator.py` の設計
3. Function Declaration の定義

**準備作業:**
- sample-sales-agent-demoのコード詳細確認
- Gemini Function Calling APIドキュメント確認
- テスト仕様書の作成

**参照ドキュメント:**
- [07_backend_migration_plan.md](07_backend_migration_plan.md) - 詳細な実装ステップ
- [12_ai_chat_implementation_plan.md](12_ai_chat_implementation_plan.md) - 現在のチャット実装
