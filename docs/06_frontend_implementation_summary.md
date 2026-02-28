# フロントエンド実装まとめ

pre-sale-sangikyo-v2 のフロントエンド実装内容を記録します。

## 実装完了日時

2026-02-28

## 技術スタック

### コア

- **Next.js 14.2.0**: App Router、Static Export
- **React 18**: Client Components
- **TypeScript**: 型安全性

### UI/スタイリング

- **Tailwind CSS v4**: `@tailwindcss/postcss` プラグイン
- **lucide-react 0.575.0**: アイコンライブラリ
- **marked**: Markdown パーサー（営業レポート表示用）
- **clsx**: クラス名結合

### 状態管理

- **@tanstack/react-query 5.90.21**: サーバー状態管理、キャッシング
- **zustand 5.0.11**: クライアント状態管理（現在未使用）

### フォーム管理

- **react-hook-form 7.71.2**: フォームバリデーション
- **@hookform/resolvers 5.2.2**: Zod連携
- **zod 4.3.6**: スキーマ定義

### UI通知

- **react-hot-toast 2.6.0**: トースト通知

### 開発ツール

- **ESLint**: コード品質チェック
- **Prettier**: コードフォーマット
- **PostCSS**: CSS処理
- **Autoprefixer**: ベンダープレフィックス自動追加

## ディレクトリ構成

```
frontend/
├── src/
│   ├── app/                           # Next.js App Router
│   │   ├── layout.tsx                 # ルートレイアウト (React Query Provider)
│   │   ├── page.tsx                   # メインチャット画面
│   │   └── globals.css                # グローバルCSS (Tailwind)
│   ├── components/                    # コンポーネント
│   │   ├── chat/                      # チャット関連
│   │   │   ├── ChatInput.tsx          # 入力フォーム
│   │   │   ├── ChatMessage.tsx        # メッセージ表示 (Markdown対応)
│   │   │   └── ProgressIndicator.tsx  # 進捗表示
│   │   ├── layout/                    # レイアウト
│   │   │   ├── Header.tsx             # ヘッダー (未使用)
│   │   │   ├── MainLayout.tsx         # メインレイアウト (Sidebar統合)
│   │   │   └── Sidebar.tsx            # サイドバー (開閉可能)
│   │   └── shared/                    # 共通コンポーネント
│   │       ├── Button.tsx             # ボタン (3variants, 3sizes)
│   │       ├── Card.tsx               # カード
│   │       └── Spinner.tsx            # スピナー
│   ├── hooks/                         # カスタムフック
│   │   ├── useAgentQuery.ts           # エージェント問い合わせ (未使用)
│   │   └── useSSE.ts                  # SSE ストリーミング
│   ├── lib/                           # ユーティリティ
│   │   ├── api/                       # API クライアント
│   │   │   └── agent.ts               # agentApi (query, queryStream, health)
│   │   └── utils.ts                   # cn() - clsx ラッパー
│   ├── types/                         # 型定義
│   │   └── agent.ts                   # QueryRequest, QueryResponse, StreamEvent
│   └── store/                         # Zustand ストア (未使用)
├── next.config.js                     # Next.js 設定 (output: 'export')
├── tsconfig.json                      # TypeScript 設定 (paths: @/*)
├── postcss.config.mjs                 # PostCSS 設定
├── eslint.config.mjs                  # ESLint 設定 (Prettier統合)
├── .prettierrc                        # Prettier 設定
└── package.json
```

## 実装した機能

### 1. メインチャット画面

**ファイル**: [src/app/page.tsx](../frontend/src/app/page.tsx)

- ユーザーが質問を入力するテキストエリア
- エージェントの応答を Markdown で表示（営業レポート形式）
- SSE (Server-Sent Events) でリアルタイムストリーミング表示
- エージェントの進捗状況表示（ツール実行状況）
- エラー表示

**主な状態管理**:
```typescript
const [messages, setMessages] = useState<Message[]>([])
const [currentQuery, setCurrentQuery] = useState<string | null>(null)
const { messages: sseEvents, isStreaming, error } = useSSE('1', currentQuery)
```

### 2. サイドバー (estyleu-fb-v1 参考)

**ファイル**: [src/components/layout/Sidebar.tsx](../frontend/src/components/layout/Sidebar.tsx)

- **開閉アニメーション**: トグルボタンでサイドバーの幅が変化（64px ↔ 256px）
- **メニューアイテム**:
  - チャット (`/`) - MessageSquare アイコン
  - データ管理 (`/data`) - Database アイコン
- **アクティブ状態**: 現在のページをハイライト表示（青色背景）
- **レスポンシブ**: 閉じた状態でもアイコンとツールチップで操作可能
- **sticky**: スクロールしても固定表示

### 3. チャット入力フォーム

**ファイル**: [src/components/chat/ChatInput.tsx](../frontend/src/components/chat/ChatInput.tsx)

- テキストエリア（3行）
- Enter キーで送信（Shift+Enter で改行）
- 送信ボタン（lucide-react の Send アイコン）
- ストリーミング中は入力無効化

### 4. メッセージ表示

**ファイル**: [src/components/chat/ChatMessage.tsx](../frontend/src/components/chat/ChatMessage.tsx)

- ユーザーメッセージ: 青色背景、プレーンテキスト
- AIメッセージ: 白色背景、Markdown レンダリング（`marked` 使用）
- アバター表示（ユーザー: 「あ」、AI: 「AI」）

### 5. 進捗インジケーター

**ファイル**: [src/components/chat/ProgressIndicator.tsx](../frontend/src/components/chat/ProgressIndicator.tsx)

- SSE イベントをリアルタイム表示
- ローディングアニメーション（Loader2 アイコン）
- 進捗メッセージのリスト表示

### 6. SSE (Server-Sent Events) カスタムフック

**ファイル**: [src/hooks/useSSE.ts](../frontend/src/hooks/useSSE.ts)

```typescript
export const useSSE = (
  userId: string,
  query: string | null
): UseSSEResult => {
  const [messages, setMessages] = useState<StreamEvent[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!query) return

    const eventSource = agentApi.queryStream(userId, query)

    eventSource.onmessage = (event) => {
      const data: StreamEvent = JSON.parse(event.data)
      setMessages((prev) => [...prev, data])

      if (data.type === 'done' || data.type === 'error') {
        eventSource.close()
        setIsStreaming(false)
      }
    }

    eventSource.onerror = (err) => {
      setError('接続エラーが発生しました')
      eventSource.close()
      setIsStreaming(false)
    }

    return () => eventSource.close()
  }, [userId, query])

  return { messages, isStreaming, error, clearMessages }
}
```

### 7. API クライアント

**ファイル**: [src/lib/api/agent.ts](../frontend/src/lib/api/agent.ts)

```typescript
export const agentApi = {
  // 通常の問い合わせ
  query: async (request: QueryRequest): Promise<QueryResponse> => {
    const res = await fetch(`${API_URL}/api/v1/sales-agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    })
    return res.json()
  },

  // SSE ストリーミング
  queryStream: (userId: string, query: string): EventSource => {
    const url = new URL(`${API_URL}/api/v1/sales-agent/query-stream`)
    url.searchParams.set('user_id', userId)
    url.searchParams.set('query', query)
    return new EventSource(url.toString())
  },

  // ヘルスチェック
  health: async (): Promise<{ status: string; initialized: boolean }> => {
    const res = await fetch(`${API_URL}/api/v1/health`)
    return res.json()
  },
}
```

## 設定ファイル詳細

### next.config.js

```javascript
const nextConfig = {
  output: 'export',  // Azure Static Web Apps 用の静的エクスポート
  images: {
    unoptimized: true,  // 静的エクスポートに必要
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "strict": true,
    "paths": {
      "@/*": ["./src/*"]  // パスエイリアス
    }
  }
}
```

### postcss.config.mjs

```javascript
const config = {
  plugins: {
    '@tailwindcss/postcss': {},  // Tailwind CSS v4
    autoprefixer: {},
  },
}
```

### eslint.config.mjs

```javascript
export default [
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      prettier: prettierPlugin,
    },
    rules: {
      'prettier/prettier': 'error',
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },
]
```

### .prettierrc

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "arrowParens": "always",
  "endOfLine": "lf"
}
```

### globals.css

```css
@import 'tailwindcss';
```

**シンプル**: Tailwind CSS v4 は設定ファイル不要、CSS インポートのみ

## 型定義

**ファイル**: [src/types/agent.ts](../frontend/src/types/agent.ts)

```typescript
export interface QueryRequest {
  user_id: string
  query: string
}

export interface QueryResponse {
  request_id: string
  user_id: string
  query: string
  response: string
  created_at: string
}

export interface StreamEvent {
  type: 'progress' | 'result' | 'error' | 'done'
  message: string
  data?: unknown
}
```

## 環境変数

### ローカル開発

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 本番環境（Azure Static Web Apps）

GitHub Secrets に設定:
```
NEXT_PUBLIC_API_URL=https://sangikyo-v2-backend.azurewebsites.net
```

## ローカル起動方法

### バックエンド (sample-sales-agent-demo)

```bash
cd /Users/estyle-0170/Environment/test/2026/02/Sangikyo-demo/sample-sales-agent-demo
source venv/bin/activate
python app/main.py
# → http://localhost:8000
```

### フロントエンド (pre-sale-sangikyo-v2)

```bash
cd /Users/estyle-0170/Environment/test/2026/02/Sangikyo-demo/pre-sale-sangikyo-v2/frontend
npm run dev
# → http://localhost:3000
```

## デプロイ

### GitHub Actions ワークフロー

**ファイル**: [.github/workflows/frontend-deploy.yml](../.github/workflows/frontend-deploy.yml)

```yaml
- name: Build Next.js app
  working-directory: frontend
  env:
    NEXT_PUBLIC_API_URL: ${{ secrets.NEXT_PUBLIC_API_URL }}
  run: npm run build

- name: Build And Deploy
  uses: Azure/static-web-apps-deploy@v1
  with:
    azure_static_web_apps_api_token: ${{ secrets.AZURE_STATIC_WEB_APPS_API_TOKEN }}
    app_location: "/frontend/out"
    output_location: ""
    skip_app_build: true
```

### デプロイURL

- **フロントエンド**: https://gentle-desert-0a11bfb00.2.azurestaticapps.net
- **バックエンド**: https://sangikyo-v2-backend.azurewebsites.net

## 未実装の機能

以下は計画されているが未実装:

1. **データ管理画面** (`/data`)
   - ユーザー情報表示
   - 担当顧客一覧
   - 商品一覧
   - 案件一覧

2. **Zustand による状態管理**
   - 現在は `useState` のみで管理
   - グローバル状態が必要になれば実装

3. **認証機能**
   - Azure AD (MSAL) は不要と判断
   - デモアプリなので認証なし

4. **エラーハンドリングの強化**
   - リトライ機能
   - より詳細なエラーメッセージ

## 参考資料

- [04_frontend_architecture_reference.md](04_frontend_architecture_reference.md) - estyleu-fb-v1 の構成
- [05_frontend_implementation_plan.md](05_frontend_implementation_plan.md) - 実装計画
- [Next.js App Router](https://nextjs.org/docs/app)
- [Tailwind CSS v4](https://tailwindcss.com/docs)
- [Server-Sent Events API](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

## トラブルシューティング

### Tailwind CSS のスタイルが適用されない

```bash
# Tailwind CSS v4 は @tailwindcss/postcss プラグインが必要
npm install --save-dev @tailwindcss/postcss tailwindcss autoprefixer
```

### SSE が接続できない

CORS 設定を確認:
```python
# backend/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://gentle-desert-0a11bfb00.2.azurestaticapps.net"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### ビルドエラー

```bash
# キャッシュをクリア
rm -rf .next node_modules
npm install
npm run build
```

## まとめ

✅ **完了した実装**
- Next.js 14 + TypeScript + Tailwind CSS v4 のモダンなフロントエンド
- SSE によるリアルタイムストリーミング対応
- Markdown レンダリングで営業レポート表示
- estyleu-fb-v1 を参考にしたサイドバー実装
- レスポンシブデザイン

🚀 **次のステップ**
- バックエンド (sample-sales-agent-demo) の機能を pre-sale-sangikyo-v2 に移植
- データ管理画面の実装（オプション）
- Azure へのデプロイと動作確認
