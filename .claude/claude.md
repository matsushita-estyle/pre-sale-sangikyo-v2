# Sangikyo V2 - 営業支援AIエージェント

## プロジェクト概要

sample-sales-agent-demoの機能をpre-sale-sangikyo-v2に段階的に移行する開発プロジェクト。

### アーキテクチャ

- **フロントエンド**: Next.js 14 (App Router) + TypeScript
- **バックエンド**: FastAPI (Python 3.x)
- **データベース**: Azure Cosmos DB (NoSQL, サーバーレスモード)
- **インフラ**: Terraform + Azure (Static Web Apps, App Service, Cosmos DB)

## コーディング規約

### フロントエンド (Next.js/React)

#### データフェッチング

- **TanStack Query (React Query) を使用する**
  - `useEffect` + `useState` の組み合わせでのデータフェッチは避ける
  - キャッシュ管理、ローディング状態、エラーハンドリングを自動化
  - 例:
    ```typescript
    const { data, isLoading, error } = useQuery({
      queryKey: ['users'],
      queryFn: getUsers,
    })
    ```

#### UI/レイアウト

- **MainLayoutコンポーネントを使用する**
  - すべてのページで`MainLayout`でラップしてサイドメニューを表示
  - 例:
    ```typescript
    return (
      <MainLayout>
        {/* ページコンテンツ */}
      </MainLayout>
    )
    ```

#### スタイリング

- Tailwind CSS v4を使用
- `@tailwindcss/postcss`を利用

#### 状態管理

- グローバル状態: Zustand
- サーバー状態: TanStack Query
- フォーム: React Hook Form + Zod

### バックエンド (FastAPI)

詳細は [Backend Architecture](../docs/10_backend_architecture.md) を参照

#### ディレクトリ構造

```
backend/
├── app/
│   ├── api/          # APIエンドポイント（HTTPハンドリング）
│   ├── core/         # コア機能（設定、DB、依存性、例外、ログ）
│   ├── models/       # Pydanticスキーマ（データモデル定義）
│   ├── repositories/ # Repository層（データアクセス）
│   ├── services/     # ビジネスロジック層（今後実装）
│   └── initializers/ # 初期化・セットアップスクリプト
├── main.py           # アプリケーションエントリーポイント
├── requirements.txt  # 依存パッケージ
└── .env              # 環境変数
```

#### レイヤーアーキテクチャ（必ず守る）

```
API層 (routes.py)
    ↓ Depends()
Repository層 (user.py, customer.py)
    ↓
Database層 (database.py)
    ↓
Cosmos DB
```

**重要な原則**:
1. **API層でデータベースに直接アクセスしない** - 必ずRepository経由
2. **Repository層でHTTPレスポンスを返さない** - データのみ返却
3. **ビジネスロジックはService層に** - Repository層は純粋なデータアクセスのみ

#### Repository パターン（必須）

**❌ 悪い例（直接Cosmos DBアクセス）**:
```python
# routes.py で直接DBアクセス（禁止）
@router.get("/users")
async def get_users():
    container = cosmos_client.get_container("Users")
    items = list(container.query_items(query="SELECT * FROM c"))
    return items
```

**✅ 良い例（Repository経由）**:
```python
# routes.py - API層
@router.get("/users", response_model=List[User])
async def get_users(repo: UserRepository = Depends(get_user_repository)):
    return await repo.get_all_users()

# repositories/user.py - Repository層
class UserRepository(BaseRepository[User]):
    async def get_all_users(self) -> List[User]:
        items = await self.get_all()
        return [User(**item) for item in items]
```

**Repository層の責任**:
- Cosmos DBへのクエリ実行
- データの取得・作成・更新・削除
- Pydanticモデルへの変換
- **ビジネスロジックは含めない**

#### Dependency注入（必須）

- `app/core/dependencies.py` でDependency関数を定義
- FastAPIの `Depends()` を使ってRepositoryを注入
- テスト時にモックRepositoryに差し替え可能

```python
# dependencies.py
def get_user_repository() -> UserRepository:
    return UserRepository()

# routes.py
@router.get("/users")
async def get_users(repo: UserRepository = Depends(get_user_repository)):
    return await repo.get_all_users()
```

#### Logging（必須）

- 全てのファイルで `import logging` して `logger = logging.getLogger(__name__)` を定義
- 主要な処理で `logger.info()`, `logger.error()` を使用
- `main.py` で `setup_logging()` を呼び出し

```python
import logging
logger = logging.getLogger(__name__)

async def get_users():
    logger.info("Fetching all users")
    users = await repo.get_all_users()
    logger.info(f"Retrieved {len(users)} users")
    return users
```

#### エラーハンドリング（推奨）

- カスタム例外クラスを使用: `NotFoundException`, `ValidationException`, `DatabaseException`
- API層でHTTPExceptionに変換

```python
# Repository層
if not user:
    raise NotFoundException(f"User {user_id} not found")

# API層
try:
    user = await repo.get_user_by_id(user_id)
    return user
except NotFoundException:
    raise HTTPException(status_code=404, detail="User not found")
```

#### 環境変数

- `.env`ファイルで管理（Gitにコミットしない）
- `app/core/config.py` で一元管理
- 必須変数:
  - `COSMOS_ENDPOINT` - Cosmos DBエンドポイント
  - `COSMOS_KEY` - Cosmos DBキー
  - `COSMOS_DATABASE_NAME` - データベース名（デフォルト: SangikyoDB）
  - `GEMINI_API_KEY` - Gemini APIキー

#### 新機能追加時の手順

1. **データモデル追加**: `app/models/schemas.py` にPydanticモデル追加
2. **Repository追加**: `app/repositories/` に新しいRepositoryクラス作成
3. **Dependency追加**: `app/core/dependencies.py` にDependency関数追加
4. **API追加**: `app/api/routes.py` にエンドポイント追加
5. **テスト**: モックRepositoryでテスト

### インフラ (Terraform)

- リソース名: `${var.project_name}-{resource_type}`
- タグ付け必須: Environment, ManagedBy, Project
- 機密情報は`sensitive = true`で出力

## 開発ワークフロー

### ローカル開発

1. **バックエンド起動**:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   # http://localhost:8000
   ```

2. **フロントエンド起動**:
   ```bash
   cd frontend
   npm run dev
   # http://localhost:3000
   ```

### デプロイ

- GitHub Actionsで自動デプロイ
- Terraformでインフラ管理

## API設計

### エンドポイント規約

- プレフィックス: `/api/v1/`
- RESTful設計
- 例:
  - `GET /api/v1/users` - ユーザー一覧取得
  - `GET /api/v1/customers` - 顧客一覧取得
  - `POST /api/v1/copilot/chat` - チャット送信

## 移行計画

詳細は `docs/07_backend_migration_plan.md` を参照

### フェーズ1: データベース統合 ✅
- Cosmos DB セットアップ
- デモデータ投入
- エンドツーエンド確認完了

### フェーズ2: エージェントツール実装（予定）
- ユーザー情報取得ツール
- 顧客検索ツール
- 案件管理ツール

### フェーズ3: LLM統合（予定）
- Gemini API統合
- プロンプトエンジニアリング

### フェーズ4: ストリーミング対応（予定）
- SSE実装
- フロントエンド進捗表示

### フェーズ5: 本番デプロイ（予定）
- Azure環境変数設定
- CI/CD最適化

## 参考資料

- [Cosmos DB Setup Guide](../docs/08_cosmosdb_setup.md)
- [Implementation Plan](../docs/09_cosmosdb_implementation_plan.md)
- [Migration Plan](../docs/07_backend_migration_plan.md)
