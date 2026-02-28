# バックエンド移植計画（段階的アプローチ）

## 目標

sample-sales-agent-demo のエージェント機能を pre-sale-sangikyo-v2 に段階的に移植し、理解しながら進める。

## データベース選択

### 選択肢

sample-sales-agent-demo では SQLite を使用していますが、以下の選択肢があります:

#### **選択肢1: Cosmos DB（推奨）**

**メリット**:
- Azure ネイティブ（本番環境に最適）
- スケーラブル
- ローカル開発でも Cosmos DB Emulator が使える
- NoSQL（JSON）で柔軟

**デメリット**:
- セットアップが少し複雑
- コスト（本番環境）

**使用するライブラリ**:
```python
azure-cosmos
pydantic
```

**データ構造（例）**:
```json
// Users コンテナ
{
  "id": "1",
  "user_id": 1,
  "name": "山田太郎",
  "email": "yamada@example.com",
  "department": "営業部",
  "attributes": {
    "industries": ["IT", "通信"],
    "regions": ["西日本"]
  }
}

// Customers コンテナ
{
  "id": "1",
  "customer_id": 1,
  "company_name": "KDDI株式会社",
  "industry": "通信系",
  "region": "西日本",
  "website": "https://www.kddi.com"
}
```

---

#### **選択肢2: SQLite（オリジナル通り）**

**メリット**:
- セットアップ不要（ファイルベース）
- sample-sales-agent-demo と同じ構造
- 理解しやすい

**デメリット**:
- Azure にデプロイする際に制約がある
- スケールしにくい

**使用するライブラリ**:
```python
sqlalchemy
```

---

#### **選択肢3: ハードコード/JSON（最もシンプル）**

**メリット**:
- データベース不要
- 最も理解しやすい
- 最も早く実装できる

**デメリット**:
- 本番環境には不向き
- データ更新が難しい

**実装例**:
```python
# data.py
USERS = [
    {
        "user_id": 1,
        "name": "山田太郎",
        "attributes": {
            "industries": ["IT", "通信"],
            "regions": ["西日本"]
        }
    }
]

CUSTOMERS = [
    {"customer_id": 1, "company_name": "KDDI", "industry": "通信系"},
    {"customer_id": 2, "company_name": "NTT西日本", "industry": "通信系"},
]
```

---

### 決定: Cosmos DB を使用

**理由**:
- Azure にデプロイする前提なので、最初から Cosmos DB を使う
- 本番環境で使える構成で学習できる
- ローカルでは Cosmos DB Emulator または Azure の無料枠を使用

**次のステップ**: Cosmos DB のセットアップから開始

## 現状分析

### sample-sales-agent-demo の構成

```
sample-sales-agent-demo/
├── app/
│   ├── main.py                 # FastAPI アプリ（lifespan で初期化）
│   ├── config.py               # 環境変数設定
│   ├── database.py             # SQLAlchemy 設定
│   ├── models.py               # DB モデル（User, Customer, Deal, Product, NewsCache）
│   ├── schemas.py              # Pydantic スキーマ
│   ├── initializer.py          # デモデータ初期化
│   ├── api/
│   │   └── routes.py           # API ルート（/health, /query, /query-stream）
│   └── agent/
│       ├── orchestrator.py     # エージェントのコアロジック（約200行）
│       ├── prompts.py          # システムプロンプト
│       └── tools.py            # ツール定義と実装（約400行）
└── requirements.txt
```

**総コード量**: 約1300行

### 主要コンポーネント

1. **データベース層** (models.py, database.py, initializer.py)
   - SQLite + SQLAlchemy
   - 5つのテーブル: User, Customer, Deal, Product, NewsCache
   - デモデータのハードコード初期化

2. **エージェント層** (agent/orchestrator.py, agent/tools.py)
   - Gemini 2.0 Flash による Function Calling
   - 4つのツール: get_user_attributes, search_customers, search_latest_news, search_products
   - 最大10イテレーション、最大3回のニュース検索

3. **API層** (api/routes.py)
   - `/api/v1/health`: ヘルスチェック
   - `/api/v1/sales-agent/query`: 通常の問い合わせ
   - `/api/v1/sales-agent/query-stream`: SSE ストリーミング問い合わせ

## 段階的移植プラン（5ステップ）

理解しながら進めるため、小さなステップに分割します。

---

## **フェーズ1: データベース基盤の構築**

**目的**: データベースとモデルの理解

### ステップ1-1: データベース設定のコピー

**作業内容**:
- `backend/app/config.py` を作成（環境変数設定）
- `backend/app/database.py` を作成（SQLAlchemy セットアップ）
- `backend/requirements.txt` に SQLAlchemy, python-dotenv を追加

**理解すべきポイント**:
- SQLAlchemy の基本（engine, session, declarative_base）
- 環境変数の管理方法

**成果物**:
- データベース接続が確立できる
- ローカルで SQLite ファイルが作成される

**確認方法**:
```bash
# Python コンソールで確認
from app.database import engine, Base
Base.metadata.create_all(bind=engine)
# → SQLite ファイルが作成される
```

---

### ステップ1-2: モデル定義のコピー

**作業内容**:
- `backend/app/models.py` を作成
- 5つのモデルをコピー: User, Customer, Deal, Product, NewsCache

**理解すべきポイント**:
- SQLAlchemy のモデル定義方法
- リレーションシップ（ForeignKey）
- 各テーブルの役割:
  - **User**: 営業担当者
  - **Customer**: 顧客企業
  - **Deal**: 案件（User と Customer の関連）
  - **Product**: 製品
  - **NewsCache**: ニュースキャッシュ

**成果物**:
- モデルが定義され、テーブルが作成できる

**確認方法**:
```bash
# Python コンソールで確認
from app.models import User, Customer
from app.database import SessionLocal

db = SessionLocal()
users = db.query(User).all()
print(users)  # → [] (空)
```

---

### ステップ1-3: デモデータ初期化

**作業内容**:
- `backend/app/initializer.py` を作成
- デモデータの投入ロジックをコピー

**理解すべきポイント**:
- どのようなデモデータが入るか
- ユーザー1名、顧客5社、案件、製品、ニュースのサンプル

**成果物**:
- スクリプト実行でデモデータが投入される

**確認方法**:
```bash
# Python コンソールで確認
from app.initializer import DataInitializer
from app.database import SessionLocal

db = SessionLocal()
initializer = DataInitializer(db)
initializer.initialize_all()

# データ確認
users = db.query(User).all()
print(f"Users: {len(users)}")  # → 1
customers = db.query(Customer).all()
print(f"Customers: {len(customers)}")  # → 5
```

---

## **フェーズ2: シンプルなAPI実装**

**目的**: FastAPI の基本とデータ取得 API の理解

### ステップ2-1: FastAPI アプリの基本セットアップ

**作業内容**:
- `backend/app/main.py` を作成（シンプル版）
- lifespan でデータベース初期化
- CORS 設定

**理解すべきポイント**:
- FastAPI の lifespan イベント
- 起動時にデータベースを初期化する仕組み

**成果物**:
- FastAPI アプリが起動する
- `/` でHello Worldが返る

**確認方法**:
```bash
cd backend
uvicorn app.main:app --reload
curl http://localhost:8000/
```

---

### ステップ2-2: データ取得 API の実装

**作業内容**:
- `backend/app/api/routes.py` を作成
- 以下のエンドポイントを実装:
  - `GET /api/v1/health`: ヘルスチェック
  - `GET /api/v1/users`: ユーザー一覧
  - `GET /api/v1/customers`: 顧客一覧
  - `GET /api/v1/products`: 製品一覧

**理解すべきポイント**:
- FastAPI の APIRouter
- Depends を使った依存性注入（get_db）
- データベースからのデータ取得

**成果物**:
- データ取得 API が動作する

**確認方法**:
```bash
curl http://localhost:8000/api/v1/health
curl http://localhost:8000/api/v1/users
curl http://localhost:8000/api/v1/customers
```

---

## **フェーズ3: エージェントツールの実装**

**目的**: Gemini Function Calling とツールの理解

### ステップ3-1: 最もシンプルなツールの実装

**作業内容**:
- `backend/app/agent/tools.py` を作成
- まず1つだけツールを実装: `get_user_attributes`

**理解すべきポイント**:
- Gemini の Function Declaration の書き方
- ツール関数の実装方法
- データベースからのデータ取得

**成果物**:
- `get_user_attributes` ツールが動作する

**確認方法**:
```python
# Python コンソールで確認
from app.agent.tools import get_user_attributes
from app.database import SessionLocal

db = SessionLocal()
result = get_user_attributes(db, user_id=1)
print(result)
# → {'担当業界': [...], '担当地域': [...]}
```

---

### ステップ3-2: 残りのツールの実装

**作業内容**:
- 残り3つのツールを実装:
  - `search_customers`: 顧客検索
  - `search_products`: 製品検索
  - `search_latest_news`: ニュース検索

**理解すべきポイント**:
- 各ツールがどのようなパラメータを受け取るか
- データベースクエリのフィルタリング方法
- ニュース検索の仕組み（キャッシュから取得）

**成果物**:
- 4つのツールすべてが動作する

**確認方法**:
```python
from app.agent.tools import search_customers

db = SessionLocal()
result = search_customers(db, industries=["IT"])
print(result)
# → 顧客リストが返る
```

---

## **フェーズ4: エージェントオーケストレーターの実装**

**目的**: Gemini Function Calling ループの理解

### ステップ4-1: システムプロンプトの設定

**作業内容**:
- `backend/app/agent/prompts.py` を作成
- システムプロンプトをコピー

**理解すべきポイント**:
- システムプロンプトがエージェントの振る舞いを決める
- 営業レポート形式の指定

**成果物**:
- システムプロンプトが定義される

---

### ステップ4-2: オーケストレーターの実装（基本版）

**作業内容**:
- `backend/app/agent/orchestrator.py` を作成
- まずは SSE なしの基本版を実装
  - Gemini API 呼び出し
  - Function Calling ループ
  - ツール実行

**理解すべきポイント**:
- Gemini の generate_content API
- Function Call の検出と実行
- ループの終了条件（最大10イテレーション）

**成果物**:
- エージェントが質問に答えられる（コンソールで確認）

**確認方法**:
```python
from app.agent.orchestrator import SalesAgentOrchestrator

agent = SalesAgentOrchestrator(api_key="YOUR_API_KEY")
result = await agent.execute_query(user_id=1, query="担当企業を教えて")
print(result)
```

---

### ステップ4-3: SSE ストリーミング対応

**作業内容**:
- `on_step` コールバックを追加
- 進捗状況をリアルタイム送信

**理解すべきポイント**:
- コールバック関数の仕組み
- どのタイミングで進捗を送信するか

**成果物**:
- 進捗状況がコールバック経由で取得できる

---

## **フェーズ5: API エンドポイントの統合**

**目的**: フロントエンドとの接続

### ステップ5-1: 通常の問い合わせエンドポイント

**作業内容**:
- `POST /api/v1/sales-agent/query` を実装
- エージェントを呼び出して結果を返す

**理解すべきポイント**:
- リクエスト/レスポンスの型定義
- エージェントの呼び出し方

**成果物**:
- curl でテストできる

**確認方法**:
```bash
curl -X POST http://localhost:8000/api/v1/sales-agent/query \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "query": "担当企業を教えて"}'
```

---

### ステップ5-2: SSE ストリーミングエンドポイント

**作業内容**:
- `POST /api/v1/sales-agent/query-stream` を実装
- StreamingResponse で SSE を返す

**理解すべきポイント**:
- FastAPI の StreamingResponse
- SSE のフォーマット（`data: {json}\n\n`）
- async generator の使い方

**成果物**:
- フロントエンドから接続できる

**確認方法**:
```bash
# curl でテスト（SSE を受信）
curl -N -X POST http://localhost:8000/api/v1/sales-agent/query-stream \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "query": "担当企業を教えて"}'
```

---

### ステップ5-3: フロントエンドとの接続確認

**作業内容**:
- ローカルでフロントエンド + バックエンドを起動
- 実際に質問して動作確認

**理解すべきポイント**:
- CORS 設定が正しいか
- フロントエンドが正しく SSE を受信できているか

**成果物**:
- エンドツーエンドで動作する

---

## 各フェーズの所要時間（目安）

| フェーズ | 内容 | 所要時間 | 理解度チェック |
|---------|------|---------|--------------|
| **フェーズ1** | データベース基盤 | 30分 | データが投入されることを確認 |
| **フェーズ2** | シンプルなAPI | 30分 | データ取得 API が動作することを確認 |
| **フェーズ3** | ツール実装 | 1時間 | 各ツールが正しく動作することを確認 |
| **フェーズ4** | オーケストレーター | 1時間 | エージェントが質問に答えることを確認 |
| **フェーズ5** | API統合 | 30分 | フロントエンドから使えることを確認 |
| **合計** | | **3.5時間** | |

## 各フェーズでの確認ポイント

### フェーズ1完了時
- [ ] SQLite ファイルが作成される
- [ ] テーブルが作成される
- [ ] デモデータが投入される
- [ ] ユーザー1名、顧客5社が確認できる

### フェーズ2完了時
- [ ] FastAPI アプリが起動する
- [ ] `/api/v1/health` が `{"status": "healthy"}` を返す
- [ ] `/api/v1/users` がユーザー一覧を返す
- [ ] `/api/v1/customers` が顧客一覧を返す

### フェーズ3完了時
- [ ] `get_user_attributes` が担当情報を返す
- [ ] `search_customers` が顧客を検索できる
- [ ] `search_products` が製品を検索できる
- [ ] `search_latest_news` がニュースを返す

### フェーズ4完了時
- [ ] エージェントが質問に答えられる（コンソール確認）
- [ ] ツールが自動で呼び出される
- [ ] 営業レポート形式で返答が返る
- [ ] 進捗コールバックが動作する

### フェーズ5完了時
- [ ] curl で問い合わせできる
- [ ] SSE でストリーミング受信できる
- [ ] フロントエンドから接続できる
- [ ] リアルタイムで進捗が表示される

## 次のステップ

このプランに同意いただければ、**フェーズ1: データベース基盤の構築** から開始します。

各ステップごとに、以下を行います:
1. コードを実装
2. 動作確認
3. 理解度チェック（質問があれば回答）
4. 次のステップへ

途中で分からないことがあれば、いつでも質問してください！
