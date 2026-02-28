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

#### ディレクトリ構造

```
backend/
├── app/
│   ├── api/          # APIエンドポイント
│   ├── core/         # 設定、DB接続
│   ├── models/       # Pydanticスキーマ
│   ├── services/     # ビジネスロジック
│   └── initializers/ # データ初期化
├── main.py           # アプリケーションエントリーポイント
├── requirements.txt
└── .env
```

#### Cosmos DB アクセス

- `app/core/database.py`のグローバル`cosmos_client`インスタンスを使用
- コンテナ名: Users, Customers, Products, Deals, News
- 例:
  ```python
  from app.core.database import cosmos_client

  container = cosmos_client.get_container("Users")
  items = list(container.query_items(
      query="SELECT * FROM c",
      enable_cross_partition_query=True
  ))
  ```

#### 環境変数

- `.env`ファイルで管理
- `python-dotenv`を使用
- 必須変数:
  - `COSMOS_ENDPOINT`
  - `COSMOS_KEY`
  - `COSMOS_DATABASE_NAME`
  - `GEMINI_API_KEY`

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
