# バックエンドアーキテクチャ

## ディレクトリ構造

```
backend/
├── app/
│   ├── api/              # APIエンドポイント層
│   ├── core/             # アプリケーションのコア機能
│   ├── models/           # データモデル定義
│   ├── repositories/     # データアクセス層
│   ├── services/         # ビジネスロジック層（今後追加予定）
│   └── initializers/     # 初期化・セットアップスクリプト
├── main.py               # アプリケーションのエントリーポイント
├── requirements.txt      # 依存パッケージリスト
└── .env                  # 環境変数
```

---

## 各ディレクトリの役割

### 1. `app/api/` - APIエンドポイント層

**役割**: HTTPリクエストを受け取り、レスポンスを返す

**含まれるファイル**:
- `routes.py` - FastAPIのルーティング定義

**責任**:
- HTTPリクエスト/レスポンスのハンドリング
- バリデーション（Pydanticモデル使用）
- Repository層を呼び出してデータ取得
- エラーハンドリング

**実装例**:
```python
@router.get("/users", response_model=List[User])
async def get_users(
    department: Optional[str] = Query(None),
    repo: UserRepository = Depends(get_user_repository),
):
    """全ユーザー取得（部署フィルタ可能）"""
    if department:
        return await repo.get_users_by_department(department)
    return await repo.get_all_users()
```

**実装済みエンドポイント**:
- `GET /api/v1/users` - ユーザー一覧（departmentやroleでフィルタ可能）
- `GET /api/v1/users/{user_id}` - 特定ユーザー取得
- `GET /api/v1/customers` - 顧客一覧（industryやsearchでフィルタ可能）
- `GET /api/v1/customers/{customer_id}` - 特定顧客取得

---

### 2. `app/core/` - コア機能

**役割**: アプリケーション全体で共通利用する設定・ユーティリティ

**含まれるファイル**:

#### `config.py` - 環境変数の読み込み、設定管理
```python
class Settings:
    COSMOS_ENDPOINT: str = os.getenv("COSMOS_ENDPOINT", "")
    COSMOS_KEY: str = os.getenv("COSMOS_KEY", "")
    COSMOS_DATABASE_NAME: str = os.getenv("COSMOS_DATABASE_NAME", "SangikyoDB")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

settings = Settings()
```

#### `database.py` - Cosmos DBクライアントの初期化
```python
class CosmosDBClient:
    def __init__(self):
        self.client = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
        self.database = self.client.get_database_client(settings.COSMOS_DATABASE_NAME)

    def get_container(self, container_name: str):
        return self.database.get_container_client(container_name)

cosmos_client = CosmosDBClient()
```

#### `dependencies.py` - FastAPIのDependency Injection設定
```python
def get_user_repository() -> UserRepository:
    return UserRepository()

def get_customer_repository() -> CustomerRepository:
    return CustomerRepository()
```

#### `exceptions.py` - カスタム例外クラス
```python
class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)

class ValidationException(AppException):
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=400)
```

#### `logging_config.py` - ログ設定
```python
def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
```

---

### 3. `app/models/` - データモデル定義

**役割**: データ構造の定義（Pydanticモデル）

**含まれるファイル**:
- `schemas.py` - API入出力のデータモデル

**責任**:
- APIリクエスト/レスポンスの型定義
- バリデーションルール定義
- データ変換

**実装例**:
```python
class User(BaseModel):
    user_id: str
    name: str
    email: str
    department: Optional[str] = None
    role: Optional[str] = None

class Customer(BaseModel):
    customer_id: str
    name: str
    industry: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
```

---

### 4. `app/repositories/` - データアクセス層（Repository パターン）

**役割**: データベースへのアクセスを抽象化

**含まれるファイル**:

#### `base.py` - 共通CRUD操作を提供するBaseRepository
```python
class BaseRepository(Generic[T]):
    def __init__(self, container_name: str):
        self.container = cosmos_client.get_container(container_name)

    async def get_all(self) -> List[dict]:
        query = "SELECT * FROM c"
        return list(self.container.query_items(query=query, enable_cross_partition_query=True))

    async def get_by_id(self, item_id: str, partition_key: str) -> Optional[dict]:
        return self.container.read_item(item=item_id, partition_key=partition_key)

    async def query(self, query: str, parameters: Optional[List] = None) -> List[dict]:
        return list(self.container.query_items(query=query, parameters=parameters or []))

    async def create(self, item: dict) -> dict:
        return self.container.create_item(body=item)

    async def upsert(self, item: dict) -> dict:
        return self.container.upsert_item(body=item)

    async def delete(self, item_id: str, partition_key: str) -> None:
        self.container.delete_item(item=item_id, partition_key=partition_key)
```

#### `user.py` - ユーザーデータアクセス
```python
class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__("Users")

    async def get_all_users(self) -> List[User]:
        items = await self.get_all()
        return [User(**item) for item in items]

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        item = await self.get_by_id(item_id=user_id, partition_key=user_id)
        return User(**item) if item else None

    async def get_users_by_department(self, department: str) -> List[User]:
        query = "SELECT * FROM c WHERE c.department = @department"
        parameters = [{"name": "@department", "value": department}]
        items = await self.query(query=query, parameters=parameters)
        return [User(**item) for item in items]
```

#### `customer.py` - 顧客データアクセス
```python
class CustomerRepository(BaseRepository[Customer]):
    def __init__(self):
        super().__init__("Customers")

    async def get_all_customers(self) -> List[Customer]:
        items = await self.get_all()
        return [Customer(**item) for item in items]

    async def get_customers_by_industry(self, industry: str) -> List[Customer]:
        query = "SELECT * FROM c WHERE c.industry = @industry"
        parameters = [{"name": "@industry", "value": industry}]
        items = await self.query(query=query, parameters=parameters)
        return [Customer(**item) for item in items]

    async def search_customers(self, keyword: str) -> List[Customer]:
        query = "SELECT * FROM c WHERE CONTAINS(c.name, @keyword)"
        parameters = [{"name": "@keyword", "value": keyword}]
        items = await self.query(query=query, parameters=parameters)
        return [Customer(**item) for item in items]
```

**Repository層の利点**:
- ビジネスロジックとデータアクセスの分離
- テストが容易（モックRepositoryを作成可能）
- データベース切り替えが簡単（Cosmos DB → SQLite など）
- クエリの再利用が容易

---

### 5. `app/services/` - ビジネスロジック層（今後追加予定）

**役割**: 複雑なビジネスロジックを実装

**将来含まれるファイル例**:
- `agent_service.py` - AIエージェントの実行ロジック
- `news_service.py` - ニュース取得ロジック
- `notification_service.py` - 通知ロジック

**責任**:
- 複数のRepositoryを組み合わせた処理
- ビジネスルールの実装
- 外部API連携（Gemini API など）

**実装イメージ（今後）**:
```python
class AgentService:
    def __init__(
        self,
        user_repo: UserRepository,
        customer_repo: CustomerRepository,
        gemini_client: GeminiClient,
    ):
        self.user_repo = user_repo
        self.customer_repo = customer_repo
        self.gemini_client = gemini_client

    async def execute_query(self, user_id: str, query: str) -> dict:
        # 1. ユーザー情報取得
        user = await self.user_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")

        # 2. ユーザーの担当業界の顧客を取得
        customers = await self.customer_repo.get_customers_by_industry(user.department)

        # 3. エージェントツールの準備
        tools = self._prepare_tools(user, customers)

        # 4. Gemini APIでエージェント実行
        result = await self.gemini_client.execute_agent(query, tools)

        return result
```

---

### 6. `app/initializers/` - 初期化スクリプト

**役割**: アプリケーション起動時やデータ初期化に使用

**含まれるファイル**:
- `seed_data.py` - デモデータの投入

**責任**:
- データベースへの初期データ投入
- セットアップスクリプト
- マイグレーション

**実装例**:
```python
def seed_users():
    """ユーザーのデモデータを投入"""
    users_container = cosmos_client.get_container("Users")
    demo_users = [
        {"id": "1", "user_id": "1", "name": "山田太郎", ...},
        {"id": "2", "user_id": "2", "name": "佐藤花子", ...},
    ]
    for user in demo_users:
        users_container.upsert_item(user)

def seed_all():
    """全てのデモデータを投入"""
    seed_users()
    seed_customers()
    seed_products()
    seed_deals()
    seed_news()
```

**実行方法**:
```bash
python -m app.initializers.seed_data
```

---

## レイヤー間のデータフロー

```
HTTP Request (GET /api/v1/users?department=営業部)
    ↓
┌──────────────────────────────────────────┐
│   app/api/routes.py                      │
│   - HTTPリクエスト受信                    │
│   - バリデーション                        │
│   - Dependencyで UserRepository 注入      │
└──────────────────────────────────────────┘
    ↓ Depends(get_user_repository)
┌──────────────────────────────────────────┐
│  app/services/agent_service.py（今後）   │
│  - 複数Repositoryを組み合わせ             │
│  - ビジネスロジック実行                   │
│  - Gemini API連携                        │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ app/repositories/user.py                 │
│  - get_users_by_department() 呼び出し     │
│  - Cosmos DBクエリ実行                    │
│  - データをPydanticモデルに変換           │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  app/core/database.py                    │
│  - Cosmos DBクライアント                  │
│  - コンテナ接続                           │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│  Azure Cosmos DB                         │
│  - SangikyoDB/Users コンテナ             │
└──────────────────────────────────────────┘
    ↓
HTTP Response (JSON: List[User])
```

---

## アーキテクチャの利点

### 1. 関心の分離（Separation of Concerns）
- API層: HTTPハンドリング
- Repository層: データアクセス
- Service層: ビジネスロジック
- 各層が独立しており、変更の影響範囲が限定的

### 2. テスト容易性
```python
# モックRepositoryでテスト可能
class MockUserRepository:
    async def get_all_users(self):
        return [User(user_id="1", name="テスト太郎", ...)]

# テスト
app.dependency_overrides[get_user_repository] = lambda: MockUserRepository()
response = client.get("/api/v1/users")
assert response.status_code == 200
```

### 3. データベース切り替えが容易
```python
# Cosmos DB → SQLite に変更する場合
class UserRepository(BaseRepository):
    def __init__(self, db_type="cosmos"):
        if db_type == "cosmos":
            super().__init__("Users")
        elif db_type == "sqlite":
            # SQLiteの実装
            pass
```

### 4. 拡張性
- 新しいエンドポイントを追加: `routes.py` に追加
- 新しいデータモデル: `repositories/` に追加
- 新しいビジネスロジック: `services/` に追加

---

## sample-sales-agent-demo との比較

| 要素 | pre-sale-sangikyo-v2 | sample-sales-agent-demo |
|------|---------------------|------------------------|
| **データベース** | Cosmos DB (NoSQL) | SQLite (SQL) |
| **ORM** | なし（直接Cosmos SDK） | SQLAlchemy |
| **Repository層** | ✅ あり（BaseRepository） | ❌ なし |
| **Service層** | （今後追加） | ❌ なし |
| **Dependency注入** | ✅ FastAPI Depends | ✅ FastAPI Depends |
| **Logging** | ✅ 構造化ログ | ✅ あり |
| **例外処理** | ✅ カスタム例外クラス | 標準HTTPException |
| **エンドポイント** | `/api/v1/users`, `/api/v1/customers` | `/api/v1/users`, `/api/v1/customers`, `/api/v1/sales-agent/query` |

**pre-sale-sangikyo-v2 の利点**:
- Repository層によりテストが容易
- レイヤーが明確で保守性が高い
- データベース切り替えが簡単
- Azure Cosmos DBでスケーラブル

---

## 今後の実装予定

### フェーズ2: エージェントツール実装
- `app/services/agent_service.py` 作成
- `app/agent/tools.py` 作成（ユーザー情報取得、顧客検索など）
- `app/agent/prompts.py` 作成

### フェーズ3: LLM統合
- Gemini API連携
- `app/services/gemini_client.py` 作成
- プロンプトエンジニアリング

### フェーズ4: ストリーミング対応
- SSE (Server-Sent Events) 実装
- `/api/v1/copilot/chat/stream` エンドポイント追加

### フェーズ5: 本番デプロイ
- Azure環境変数設定
- CI/CD最適化
- パフォーマンスチューニング

---

## 参考資料

- [Cosmos DB Setup Guide](08_cosmosdb_setup.md)
- [Implementation Plan](09_cosmosdb_implementation_plan.md)
- [Migration Plan](07_backend_migration_plan.md)
- [Project Architecture](.claude/claude.md)
