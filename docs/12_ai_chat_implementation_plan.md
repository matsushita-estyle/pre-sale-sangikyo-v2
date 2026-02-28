# AI チャット機能実装プラン

## 概要

営業支援AIエージェントの核となるチャット機能を段階的に実装します。エージェント機能の前に、まず基本的なチャット機能を確実に動作させることを優先します。

## 実装ステップ

### **ステップ1: シンプルなチャット機能（エージェント無し）** ⭐️ 開始地点

まずは基本的なチャット機能を動かす：

```
ユーザー入力 → バックエンドAPI → Gemini API → レスポンス返却
```

**実装内容:**
- `/api/v1/copilot/chat` エンドポイント作成（非ストリーミング）
- Gemini APIの基本的な質問応答
- Cosmos DBデータは**まだ使わない**（ただのチャットボット）
- シンプルなプロンプトで動作確認

**メリット:**
- 最小構成で動作確認できる
- Gemini API接続のトラブルシュートが簡単
- フロントエンドとの疎通確認が容易
- 問題の切り分けがしやすい

**実装ファイル:**
- `backend/app/api/routes.py` - エンドポイント追加
- `backend/app/services/copilot_service.py` - Gemini API呼び出しロジック
- 環境変数: `GEMINI_API_KEY`

**テスト方法:**
```bash
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1","query":"こんにちは"}'
```

**所要時間:** 30分〜1時間

---

### **ステップ2: RAG機能追加（Cosmos DBデータ活用）**

Gemini APIにDeals/Customers/Usersデータを渡す：

```
ユーザー入力 → Cosmos DB検索 → コンテキスト作成 → Gemini API → レスポンス
```

**実装内容:**
- Repositoryを使ってユーザーの担当案件を取得
- 顧客情報、案件情報をコンテキストとして取得
- プロンプトにデータを埋め込む
- 「あなたの担当案件は...」のような回答を生成

**プロンプト例:**
```
あなたは営業支援AIアシスタントです。
以下のデータを元に質問に答えてください。

【担当案件】
- KDDI株式会社: 5G基地局構築（商談中、5000万円）
- ソフトバンク: 人材派遣（提案中、3000万円）

【質問】
{user_query}
```

**メリット:**
- 実用的な回答が返るようになる
- ユーザー固有のデータに基づいた提案が可能
- sample-sales-agent-demoの `copilot_service.py` を参考にできる

**実装ファイル:**
- `backend/app/services/copilot_service.py` - コンテキスト取得ロジック追加
- Dependency Injection で Repository を注入

**テスト方法:**
```bash
curl -X POST http://localhost:8000/api/v1/copilot/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1","query":"私の担当案件を教えて"}'
```

**所要時間:** 1〜2時間

---

### **ステップ3: ストリーミング対応**

リアルタイムで回答が表示されるように：

```
SSE (Server-Sent Events) でストリーミング配信
```

**実装内容:**
- `/api/v1/copilot/chat/stream` エンドポイント作成
- Gemini APIのストリーミングレスポンスを転送
- フロントエンドの `useSSE` フック修正
- `StreamingResponse` を使用したSSE実装

**SSE イベント形式:**
```
data: {"type":"progress","message":"データを取得中..."}

data: {"type":"content","message":"あなたの担当案件は"}

data: {"type":"content","message":"KDDI株式会社の"}

data: {"type":"result","message":"完全な回答テキスト"}

data: {"type":"done"}
```

**メリット:**
- ChatGPT風のUX
- 回答が長くても待たせない
- 進捗状況をリアルタイムで表示

**実装ファイル:**
- `backend/app/api/routes.py` - ストリーミングエンドポイント
- `frontend/src/hooks/useSSE.ts` - SSEフック修正

**テスト方法:**
```bash
curl -N http://localhost:8000/api/v1/copilot/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"user_id":"1","query":"私の担当案件を教えて"}'
```

**所要時間:** 1〜2時間

---

### **ステップ4: Durable Functions（エージェント機能）** ← 後回し可

複雑なタスクを段階的に実行：

```
ユーザー入力 → タスク分解 → 複数ステップ実行 → 結果統合
```

**実装内容:**
- Azure Durable Functions のオーケストレーター
- タスク分解ロジック（Gemini APIでタスクを生成）
- 複数ステップの実行と進捗管理
- 中間結果の保存と最終結果の統合

**エージェント動作例:**
```
ユーザー: 「KDDI向けに5G基地局構築の提案書を作成して」

ステップ1: 顧客情報取得 → 進捗: "KDDI株式会社の情報を取得中..."
ステップ2: 競合分析    → 進捗: "競合他社の提案を分析中..."
ステップ3: 提案書生成  → 進捗: "提案書を作成中..."
ステップ4: 結果返却    → 完了: "提案書が完成しました"
```

**メリット:**
- 「競合分析して提案書を作成」のような複雑タスクに対応
- sample-sales-agent-demoの最大の特徴
- タスクの進捗が可視化される

**実装ファイル:**
- `backend/function_app.py` - Durable Functions定義
- `backend/app/services/agent_service.py` - エージェントロジック
- `backend/app/services/orchestrator.py` - タスクオーケストレーション

**注意点:**
- Azure Functions のローカル実行環境が必要
- デバッグが複雑
- 実装とテストに時間がかかる

**所要時間:** 3〜5時間（複雡）

---

## 推奨実装順序

```
✅ ステップ1（基本チャット）
   ↓ 動作確認OK
✅ ステップ2（RAG追加）
   ↓ 実用的な回答が返る
✅ ステップ3（ストリーミング）
   ↓ UX改善
⭕ ステップ4（エージェント）← デモに必要な場合のみ
```

**理由:**
- ステップ1〜3で既に十分実用的なAI営業支援ツールになる
- エージェント機能は「あれば凄い」だが「必須ではない」
- sample-sales-agent-demoのエージェント部分は複雑で、デバッグに時間がかかる可能性が高い
- まずは確実に動く基盤を作ることを優先

---

## 参考実装

### sample-sales-agent-demo の構造

```
backend/
├── function_app.py              # Azure Functions エントリーポイント
├── app/
│   ├── services/
│   │   ├── copilot_service.py   # チャット機能（ステップ1-3）
│   │   └── agent_service.py     # エージェント機能（ステップ4）
│   ├── models/
│   │   └── chat_models.py       # リクエスト/レスポンスモデル
│   └── utils/
│       └── gemini_client.py     # Gemini API ラッパー
```

### 環境変数

```bash
GEMINI_API_KEY=<Google AI Studio APIキー>
COSMOS_ENDPOINT=<Cosmos DB エンドポイント>
COSMOS_KEY=<Cosmos DB キー>
```

---

## 成果物

### ステップ1-3 完了時点

- ✅ ユーザーがチャットで質問できる
- ✅ 担当案件に基づいた回答が返る
- ✅ ストリーミングでリアルタイム表示
- ✅ 実用的な営業支援ツールとして機能

**実現できる質問例:**
- 「私の担当案件を教えて」
- 「商談中の案件で注意すべきものは？」
- 「KDDI向けに次に提案すべきサービスは？」
- 「失注案件の傾向を分析して」

### ステップ4 完了時点

- ✅ 上記に加えて
- ✅ 複数ステップのタスク実行
- ✅ 進捗状況の可視化
- ✅ 提案書や分析レポートの自動生成

---

## 次のアクション

**まずステップ1から開始:**
1. Gemini API キーの取得・設定
2. `copilot_service.py` の作成
3. `/api/v1/copilot/chat` エンドポイントの実装
4. 基本的なチャット機能の動作確認

**完了したらステップ2へ進む**
