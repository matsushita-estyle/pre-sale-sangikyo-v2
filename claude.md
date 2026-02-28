# Claude Code ガイドライン

このプロジェクトでClaude Codeを使用する際のガイドラインです。

## 技術スタック

### フロントエンド
- **フレームワーク**: Next.js 15 (App Router)
- **言語**: TypeScript
- **状態管理**: Zustand (グローバル状態管理用)
- **データフェッチ**: TanStack Query (React Query)
- **スタイリング**: Tailwind CSS
- **アイコン**: Lucide React

### バックエンド
- **フレームワーク**: FastAPI
- **言語**: Python 3.10+
- **AI**: Google Gemini API
- **データベース**: Azure Cosmos DB

## コーディング規約

### 状態管理

**Zustandを使用してください**

グローバルな状態管理にはZustandを使用します。Context APIは使用しないでください。

```typescript
// ✅ Good: Zustandを使用
import { create } from 'zustand'

interface UserStore {
  selectedUserId: string
  setSelectedUserId: (userId: string) => void
}

export const useUserStore = create<UserStore>((set) => ({
  selectedUserId: '1',
  setSelectedUserId: (userId) => set({ selectedUserId: userId }),
}))

// コンポーネントで使用
const selectedUserId = useUserStore((state) => state.selectedUserId)
const { setSelectedUserId } = useUserStore()
```

```typescript
// ❌ Bad: Context APIは使用しない
const UserContext = createContext<UserContextType | undefined>(undefined)
```

### データフェッチング

**TanStack Query (React Query) を使用してください**

```typescript
// ✅ Good: TanStack Queryを使用
import { useQuery } from '@tanstack/react-query'

const { data: users = [], isLoading } = useQuery({
  queryKey: ['users'],
  queryFn: getUsers,
})
```

```typescript
// ❌ Bad: useEffect + fetchは使用しない
useEffect(() => {
  fetch('/api/users').then(...)
}, [])
```

### ファイル構成

```
frontend/src/
├── app/              # Next.js App Router pages
├── components/       # Reactコンポーネント
│   ├── chat/        # チャット関連
│   ├── layout/      # レイアウト関連
│   └── shared/      # 共通コンポーネント
├── lib/             # ユーティリティ・API
└── store/           # Zustand stores
```

### コンポーネントの書き方

- クライアントコンポーネントには `'use client'` を付ける
- サーバーコンポーネントはデフォルトで使用
- propsの型定義は必須

```typescript
'use client'

interface ButtonProps {
  onClick: () => void
  children: React.ReactNode
}

export function Button({ onClick, children }: ButtonProps) {
  // ...
}
```

## 新機能追加時のチェックリスト

- [ ] TypeScriptの型定義は適切か
- [ ] 状態管理にZustandを使用しているか
- [ ] データフェッチにTanStack Queryを使用しているか
- [ ] Tailwind CSSでスタイリングしているか
- [ ] エラーハンドリングは適切か

## 参考

- [Next.js Documentation](https://nextjs.org/docs)
- [Zustand Documentation](https://docs.pmnd.rs/zustand/getting-started/introduction)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
