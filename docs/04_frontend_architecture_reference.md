# フロントエンド構成リファレンス (estyleu-fb-v1)

このドキュメントでは、estyleu-fb-v1 のフロントエンド構成を参考資料としてまとめます。
pre-sale-sangikyo-v2 のフロントエンドを構築する際の参考にしてください。

## プロジェクト概要

- **フレームワーク**: Next.js 16 (App Router)
- **言語**: TypeScript
- **スタイリング**: Tailwind CSS v4
- **状態管理**: Zustand + React Query (TanStack Query)
- **認証**: Azure AD (MSAL)
- **フォーム**: React Hook Form + Zod
- **UI通知**: React Hot Toast
- **デプロイ**: Azure App Service (standalone mode)

## ディレクトリ構成

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── (auth)/              # 認証が必要なページ (Route Group)
│   │   │   ├── dashboard/       # ダッシュボード
│   │   │   ├── feedback/        # フィードバック関連
│   │   │   │   ├── list/
│   │   │   │   ├── new/
│   │   │   │   ├── edit/
│   │   │   │   └── upload/
│   │   │   └── layout.tsx       # 認証レイアウト
│   │   ├── design/              # デザインシステムプレビュー
│   │   ├── layout.tsx           # ルートレイアウト
│   │   ├── page.tsx             # トップページ
│   │   ├── auth-provider.tsx    # 認証プロバイダー
│   │   └── globals.css          # グローバルCSS
│   ├── components/              # コンポーネント
│   │   ├── auth/                # 認証関連コンポーネント
│   │   │   ├── auth-guard.tsx
│   │   │   └── login-button.tsx
│   │   ├── layout/              # レイアウトコンポーネント
│   │   │   ├── MainLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   └── user-menu.tsx
│   │   ├── feedback/            # ドメイン固有コンポーネント
│   │   │   ├── FeedbackTable.tsx
│   │   │   ├── OriginalDataTab.tsx
│   │   │   └── AIFeedbackTab.tsx
│   │   ├── shared/              # 共通コンポーネント
│   │   └── ui/                  # UIプリミティブ (存在するが空)
│   ├── hooks/                   # カスタムフック
│   │   ├── use-auth.ts
│   │   ├── useFeedback.ts
│   │   └── useFeedbacks.ts
│   ├── lib/                     # ユーティリティ
│   │   ├── api/                 # API クライアント
│   │   │   └── feedback.ts
│   │   ├── utils.ts             # clsx ラッパー
│   │   └── msal-config.ts       # Azure AD 設定
│   ├── providers/               # グローバルプロバイダー
│   │   └── QueryProvider.tsx    # React Query Provider
│   ├── server/                  # Server Actions / Services
│   │   ├── actions/
│   │   └── services/
│   ├── store/                   # Zustand ストア
│   │   └── feedbackStore.ts
│   ├── types/                   # 型定義
│   │   ├── auth.ts
│   │   └── feedback.ts
│   └── constants/               # 定数
├── .husky/                      # Git hooks
├── .env.local                   # 環境変数
├── next.config.js
├── tsconfig.json
├── eslint.config.mjs
├── postcss.config.mjs
├── .prettierrc
├── .lintstagedrc.json
└── package.json
```

## 主要ライブラリ

### コア依存関係

```json
{
  "dependencies": {
    "next": "^16.1.6",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "typescript": "^5"
  }
}
```

### 認証

```json
{
  "@azure/msal-browser": "^5.2.0",
  "@azure/msal-react": "^5.0.4"
}
```

**用途**: Azure AD (Microsoft Entra ID) による SSO 認証

### 状態管理

```json
{
  "@tanstack/react-query": "^5.90.21",
  "zustand": "^5.0.11"
}
```

- **React Query**: サーバー状態管理、キャッシング、再フェッチ
- **Zustand**: クライアント状態管理 (軽量、シンプル)

### フォーム管理

```json
{
  "react-hook-form": "^7.71.2",
  "@hookform/resolvers": "^5.2.2",
  "zod": "^4.3.6"
}
```

**用途**: フォームバリデーション、型安全なスキーマ定義

### UI/UX

```json
{
  "tailwindcss": "^4.2.0",
  "@tailwindcss/postcss": "^4.2.0",
  "lucide-react": "^0.575.0",
  "react-hot-toast": "^2.6.0",
  "clsx": "^2.1.1",
  "date-fns": "^4.1.0"
}
```

- **Tailwind CSS v4**: ユーティリティファーストCSS
- **lucide-react**: アイコンライブラリ
- **react-hot-toast**: 通知トースト
- **clsx**: クラス名結合ユーティリティ
- **date-fns**: 日付操作

### 開発ツール

```json
{
  "devDependencies": {
    "@typescript-eslint/eslint-plugin": "^8.56.0",
    "@typescript-eslint/parser": "^8.56.0",
    "eslint": "^9.39.3",
    "eslint-config-next": "^16.1.6",
    "eslint-config-prettier": "^10.1.8",
    "eslint-plugin-prettier": "^5.5.5",
    "prettier": "^3.8.1",
    "husky": "^9.1.7",
    "lint-staged": "^16.2.7"
  }
}
```

## 設定ファイル詳細

### next.config.js

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',  // Azure App Service 用
}

module.exports = nextConfig
```

**重要**: `standalone` モードは Azure App Service へのデプロイに最適化。
Static Web Apps の場合は `export` を使用。

### tsconfig.json

```json
{
  "compilerOptions": {
    "strict": true,
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "jsx": "react-jsx",
    "moduleResolution": "bundler",
    "paths": {
      "@/*": ["./src/*"]  // エイリアス設定
    }
  }
}
```

**ポイント**: `@/` エイリアスで `src/` 配下をインポート可能

### eslint.config.mjs

```javascript
export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.{js,jsx,ts,tsx}'],
    plugins: {
      react,
      prettier: prettierPlugin,
    },
    rules: {
      'prettier/prettier': 'error',
      'react/react-in-jsx-scope': 'off',  // Next.js では不要
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
    },
  },
]
```

**特徴**: ESLint v9 フラット設定、Prettier 統合

### .prettierrc

```json
{
  "semi": false,          // セミコロンなし
  "singleQuote": true,    // シングルクォート
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 80,
  "arrowParens": "always",
  "endOfLine": "lf"
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

**注意**: Tailwind CSS v4 は `@tailwindcss/postcss` プラグインを使用

### globals.css

```css
@import 'tailwindcss';
```

**シンプル**: Tailwind CSS v4 は設定ファイル不要、CSS インポートのみ

## アーキテクチャパターン

### 1. App Router (Next.js 14+)

```
app/
├── layout.tsx           # ルートレイアウト
├── page.tsx             # トップページ
└── (auth)/              # Route Group (URLに影響しない)
    ├── layout.tsx       # 認証レイアウト (共通サイドバー等)
    └── dashboard/
        └── page.tsx     # /dashboard
```

**Route Groups `(auth)`**: URL に含まれず、レイアウト共有のみ

### 2. 認証フロー

```typescript
// app/layout.tsx
<QueryProvider>
  <AuthProvider>     // MSAL 初期化
    {children}
  </AuthProvider>
</QueryProvider>

// app/(auth)/layout.tsx
<AuthGuard>          // 認証チェック
  <MainLayout>       // サイドバー等
    {children}
  </MainLayout>
</AuthGuard>
```

### 3. 状態管理パターン

```typescript
// サーバー状態: React Query
const { data, isLoading } = useFeedbacks()  // 自動キャッシュ、再フェッチ

// クライアント状態: Zustand
const { selectedId, setSelectedId } = useFeedbackStore()
```

### 4. フォームバリデーション

```typescript
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'

const schema = z.object({
  name: z.string().min(1, '必須です'),
})

const form = useForm({
  resolver: zodResolver(schema),
})
```

### 5. API クライアント

```typescript
// lib/api/feedback.ts
export const feedbackApi = {
  getAll: async () => {
    const res = await fetch(`${API_URL}/feedbacks`)
    return res.json()
  },
}

// hooks/useFeedbacks.ts
export const useFeedbacks = () => {
  return useQuery({
    queryKey: ['feedbacks'],
    queryFn: feedbackApi.getAll,
  })
}
```

## Git Hooks (Husky + lint-staged)

### .lintstagedrc.json

```json
{
  "*.{ts,tsx,js,jsx}": [
    "eslint --fix",
    "prettier --write"
  ]
}
```

**動作**: コミット前に自動で lint + format

## npm スクリプト

```json
{
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start -p 8080",
    "lint": "eslint --ext .ts,.tsx,.js,.jsx src/",
    "lint:fix": "eslint --ext .ts,.tsx,.js,.jsx src/ --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,js,jsx,json,css,md}\"",
    "format:check": "prettier --check \"src/**/*.{ts,tsx,js,jsx,json,css,md}\""
  }
}
```

## pre-sale-sangikyo-v2 への適用推奨事項

### ✅ 採用すべき構成

1. **ディレクトリ構造**: `app/`, `components/`, `hooks/`, `lib/`, `types/` の分離
2. **状態管理**: React Query (サーバー状態) + Zustand (クライアント状態)
3. **フォーム**: React Hook Form + Zod
4. **スタイリング**: Tailwind CSS v4
5. **型安全性**: TypeScript strict mode
6. **開発体験**: ESLint + Prettier + Husky
7. **パスエイリアス**: `@/*` で `src/*` を参照

### ⚠️ 調整が必要な箇所

1. **認証**: Azure AD (MSAL) → 不要の可能性（サンプルアプリ）
2. **デプロイモード**: `standalone` → `export` (Static Web Apps 用)
3. **ドメインロジック**: フィードバック管理 → 営業支援エージェント

### 📦 最小構成での開始

```json
{
  "dependencies": {
    "next": "^16.1.6",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "@tanstack/react-query": "^5.90.21",
    "react-hook-form": "^7.71.2",
    "@hookform/resolvers": "^5.2.2",
    "zod": "^4.3.6",
    "react-hot-toast": "^2.6.0",
    "lucide-react": "^0.575.0",
    "clsx": "^2.1.1",
    "date-fns": "^4.1.0"
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4.2.0",
    "tailwindcss": "^4.2.0",
    "typescript": "^5",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "eslint": "^9.39.3",
    "eslint-config-next": "^16.1.6",
    "prettier": "^3.8.1"
  }
}
```

## 参考リンク

- **Next.js App Router**: https://nextjs.org/docs/app
- **Tailwind CSS v4**: https://tailwindcss.com/docs
- **React Query**: https://tanstack.com/query/latest
- **Zustand**: https://zustand.docs.pmnd.rs/
- **React Hook Form**: https://react-hook-form.com/
- **Zod**: https://zod.dev/

## まとめ

estyleu-fb-v1 は以下の特徴を持つモダンな Next.js アプリケーション:

- **App Router**: ファイルベースルーティング、Route Groups
- **TypeScript**: 型安全性、開発体験の向上
- **Tailwind CSS v4**: ユーティリティファーストCSS
- **React Query + Zustand**: 効率的な状態管理
- **開発ツール充実**: ESLint, Prettier, Husky で品質保証

pre-sale-sangikyo-v2 でも同様のアーキテクチャを採用することで、保守性と開発体験が向上します。
