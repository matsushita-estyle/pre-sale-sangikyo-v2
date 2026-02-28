# フロントエンド実装計画

## 目標

sample-sales-agent-demo の機能を Next.js + TypeScript で再実装し、Azure Static Web Apps にデプロイする。

## 実装する機能

### 1. メインチャット画面

- ユーザーが質問を入力できるテキストエリア
- エージェントの応答をMarkdownで表示（営業レポート形式）
- SSE (Server-Sent Events) でリアルタイムストリーミング表示
- エージェントの進捗状況表示（ツール実行状況）

### 2. データ表示画面（オプション）

- ユーザー情報
- 担当顧客一覧
- 商品一覧
- 案件一覧

## 技術スタック

### コアライブラリ

- **Next.js 16**: App Router
- **React 19**: 最新版
- **TypeScript**: 型安全性

### UI/スタイリング

- **Tailwind CSS v4**: ユーティリティファーストCSS
- **lucide-react**: アイコンライブラリ
- **react-hot-toast**: 通知トースト
- **clsx**: クラス名結合
- **marked**: Markdown パーサー（営業レポート表示用）

### 状態管理

- **@tanstack/react-query**: サーバー状態管理、キャッシング
- **zustand**: クライアント状態管理（軽量）

### フォーム管理

- **react-hook-form**: フォームバリデーション
- **@hookform/resolvers**: Zod連携
- **zod**: スキーマ定義

### 開発ツール

- **ESLint**: コード品質チェック
- **Prettier**: コードフォーマット
- **Husky + lint-staged**: Git hooks（コミット前チェック）

## ディレクトリ構成

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── layout.tsx          # ルートレイアウト
│   │   ├── page.tsx            # メインチャット画面
│   │   ├── data/               # データ表示画面（オプション）
│   │   │   └── page.tsx
│   │   └── globals.css         # グローバルCSS
│   ├── components/             # コンポーネント
│   │   ├── chat/               # チャット関連
│   │   │   ├── ChatInput.tsx   # 入力フォーム
│   │   │   ├── ChatMessage.tsx # メッセージ表示
│   │   │   └── ProgressIndicator.tsx # 進捗表示
│   │   ├── layout/             # レイアウト
│   │   │   └── Header.tsx
│   │   └── shared/             # 共通コンポーネント
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       └── Spinner.tsx
│   ├── hooks/                  # カスタムフック
│   │   ├── useAgentQuery.ts    # エージェント問い合わせ
│   │   └── useSSE.ts           # SSE ストリーミング
│   ├── lib/                    # ユーティリティ
│   │   ├── api/                # API クライアント
│   │   │   └── agent.ts
│   │   └── utils.ts            # clsx ラッパー
│   ├── types/                  # 型定義
│   │   ├── agent.ts
│   │   └── data.ts
│   └── store/                  # Zustand ストア
│       └── chatStore.ts
├── next.config.js              # Next.js 設定
├── tsconfig.json               # TypeScript 設定
├── tailwind.config.ts          # Tailwind CSS 設定
├── postcss.config.mjs          # PostCSS 設定
├── eslint.config.mjs           # ESLint 設定
├── .prettierrc                 # Prettier 設定
└── package.json
```

## API エンドポイント（バックエンド）

sample-sales-agent-demo のエンドポイント:

```
GET  /api/v1/health                    # ヘルスチェック
GET  /api/v1/data-status               # データ初期化状態
GET  /api/v1/users                     # ユーザー一覧
POST /api/v1/sales-agent/query         # エージェント問い合わせ
POST /api/v1/sales-agent/query-stream  # SSE ストリーミング問い合わせ
POST /api/v1/sales-agent/upload-pdf    # PDF アップロード
```

## 実装ステップ

### ステップ1: 環境構築

```bash
cd frontend
npm install --save \
  @tanstack/react-query \
  zustand \
  react-hook-form \
  @hookform/resolvers \
  zod \
  react-hot-toast \
  lucide-react \
  clsx \
  marked

npm install --save-dev \
  @tailwindcss/postcss \
  tailwindcss \
  autoprefixer \
  prettier \
  eslint-config-prettier \
  eslint-plugin-prettier \
  husky \
  lint-staged
```

### ステップ2: 設定ファイル

- **tailwind.config.ts**: Tailwind CSS v4 設定
- **postcss.config.mjs**: PostCSS プラグイン
- **eslint.config.mjs**: ESLint フラット設定
- **.prettierrc**: Prettier ルール
- **tsconfig.json**: パスエイリアス `@/*`

### ステップ3: 基本コンポーネント

- Button, Card, Spinner などの共通UI
- Header レイアウト

### ステップ4: API クライアント

```typescript
// lib/api/agent.ts
export const agentApi = {
  query: async (userId: string, query: string) => {
    const res = await fetch(`${API_URL}/api/v1/sales-agent/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, query }),
    })
    return res.json()
  },

  queryStream: (userId: string, query: string) => {
    return new EventSource(
      `${API_URL}/api/v1/sales-agent/query-stream?user_id=${userId}&query=${encodeURIComponent(query)}`
    )
  },
}
```

### ステップ5: カスタムフック

```typescript
// hooks/useAgentQuery.ts
export const useAgentQuery = () => {
  return useMutation({
    mutationFn: ({ userId, query }: { userId: string; query: string }) =>
      agentApi.query(userId, query),
  })
}

// hooks/useSSE.ts
export const useSSE = (userId: string, query: string | null) => {
  const [messages, setMessages] = useState<string[]>([])
  const [isStreaming, setIsStreaming] = useState(false)

  useEffect(() => {
    if (!query) return

    const eventSource = agentApi.queryStream(userId, query)
    setIsStreaming(true)

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setMessages((prev) => [...prev, data.content])
    }

    eventSource.onerror = () => {
      eventSource.close()
      setIsStreaming(false)
    }

    return () => eventSource.close()
  }, [userId, query])

  return { messages, isStreaming }
}
```

### ステップ6: メインチャット画面

```typescript
// app/page.tsx
'use client'

export default function ChatPage() {
  const [query, setQuery] = useState('')
  const [currentQuery, setCurrentQuery] = useState<string | null>(null)
  const { messages, isStreaming } = useSSE('1', currentQuery)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    setCurrentQuery(query)
  }

  return (
    <div>
      <ChatMessages messages={messages} />
      <ChatInput
        value={query}
        onChange={setQuery}
        onSubmit={handleSubmit}
        disabled={isStreaming}
      />
    </div>
  )
}
```

### ステップ7: Markdown 表示

```typescript
// components/chat/ChatMessage.tsx
import { marked } from 'marked'

export function ChatMessage({ content }: { content: string }) {
  const html = marked(content)

  return (
    <div
      className="prose"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
```

### ステップ8: SSE ストリーミング

- Server-Sent Events (EventSource API) を使用
- リアルタイムで進捗状況を表示
- エラーハンドリング

### ステップ9: ローカルテスト

```bash
# バックエンド起動（ポート8000）
cd sample-sales-agent-demo
python app/main.py

# フロントエンド起動（ポート3000）
cd pre-sale-sangikyo-v2/frontend
npm run dev
```

### ステップ10: デプロイ

- GitHub Actions で自動デプロイ
- 環境変数 `NEXT_PUBLIC_API_URL` を設定

## 注意事項

### Next.js Static Export の制限

- `output: 'export'` では Server Components が使えない
- すべて Client Component (`'use client'`) にする必要あり
- API Routes は使えない（外部バックエンドを使用）

### SSE (Server-Sent Events) の扱い

- EventSource API はブラウザネイティブ
- クローズ処理を忘れずに
- エラーハンドリングを適切に実装

### CORS 設定

バックエンドで Static Web Apps のオリジンを許可:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://gentle-desert-0a11bfb00.2.azurestaticapps.net",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 成果物

- ✅ モダンな Next.js + TypeScript フロントエンド
- ✅ リアルタイムストリーミング対応
- ✅ Tailwind CSS によるレスポンシブデザイン
- ✅ 型安全な API 通信
- ✅ Azure Static Web Apps へのデプロイ

## 参考資料

- [04_frontend_architecture_reference.md](04_frontend_architecture_reference.md)
- [sample-sales-agent-demo の実装](../sample-sales-agent-demo/)
- [Next.js App Router](https://nextjs.org/docs/app)
- [Server-Sent Events API](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
