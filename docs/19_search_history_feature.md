# 検索履歴機能の実装

**作成日**: 2026-03-01
**機能概要**: エージェントが実行したツール呼び出し（検索）の履歴を、回答完了後も確認できる機能

## 1. 要件と設計

### ユーザー要望
- エージェントの検索が終わった後、実行した検索履歴を確認できるようにしたい
- Claude Code風の薄いグレー色のアコーディオン形式で表示
- 検索履歴は回答の上に配置
- 検索中の進捗表示も同じ薄いグレー色に統一

### デザイン方針（採用案：アコーディオン形式）

```
▶ 実行した検索 (3件)  ← 薄いグレー、折りたたみ可能
[回答内容]            ← Markdown形式の回答
```

**展開時:**
```
▼ 実行した検索 (3件)

  search_customers
  引数: industries: ["IT", "通信"]
  結果: 3件の顧客が見つかりました

  search_latest_news
  引数: keywords: ["KDDI"]
  結果: 5件のニュースを取得しました

[回答内容]
```

### UIスタイル仕様
- 背景色: `bg-gray-50`
- ボーダー: `border border-gray-200`
- テキスト: `text-gray-600` (薄い文字)
- アイコン: `▶` (閉じている) / `▼` (開いている)
- ホバー: `hover:bg-gray-100`

## 2. 実装内容

### 2.1 型定義の追加

**ファイル**: `frontend/src/types/agent.ts`

```typescript
// 検索履歴アイテム
export interface SearchHistoryItem {
  toolName: string
  arguments: Record<string, any>
  result: string
}
```

**ファイル**: `frontend/src/app/page.tsx`, `frontend/src/components/chat/ChatMessages.tsx`

```typescript
interface Message {
  role: 'user' | 'assistant'
  content: string
  searchHistory?: SearchHistoryItem[]  // NEW
}
```

### 2.2 検索履歴の抽出・保存ロジック

**ファイル**: `frontend/src/hooks/useAgentStream.ts`

**変更点:**
1. `AgentStreamState`に`searchHistory: SearchHistoryItem[]`を追加
2. `function_call`と`function_result`のペアを記録するために`Map`を使用
3. `function_call`イベントが来たら、ツール名と引数を`Map`に保存
4. `function_result`イベントが来たら、`Map`から対応する`function_call`を取得し、`searchHistory`に追加

**実装コード:**
```typescript
interface AgentStreamState {
  events: ProgressEvent[]
  currentMessage: string
  finalResponse: string | null
  searchHistory: SearchHistoryItem[]  // NEW
  isLoading: boolean
  error: string | null
}

const sendQuery = useCallback(async (userId: string, query: string) => {
  setState({
    events: [],
    currentMessage: '',
    finalResponse: null,
    searchHistory: [],  // NEW
    isLoading: true,
    error: null,
  })

  // function_callとfunction_resultのペアを保存するための一時マップ
  const functionCallMap = new Map<string, { arguments: Record<string, any> }>()

  // ... SSEストリーム処理 ...

  // function_callを記録
  if (progressEvent.type === 'function_call' && progressEvent.tool_name) {
    functionCallMap.set(progressEvent.tool_name, {
      arguments: progressEvent.arguments || {},
    })
  }

  // function_resultが来たら検索履歴に追加
  if (progressEvent.type === 'function_result' && progressEvent.tool_name) {
    const toolName = progressEvent.tool_name
    const functionCall = functionCallMap.get(toolName)
    if (functionCall) {
      setState((prev) => ({
        ...prev,
        searchHistory: [
          ...prev.searchHistory,
          {
            toolName,
            arguments: functionCall.arguments,
            result: progressEvent.result || '',
          },
        ],
      }))
      functionCallMap.delete(toolName)
    }
  }
}, [])
```

### 2.3 SearchHistoryコンポーネントの作成

**ファイル**: `frontend/src/components/agent/SearchHistory.tsx` (NEW)

**機能:**
- アコーディオン形式の検索履歴表示
- デフォルトは折りたたみ状態
- クリックで展開/折りたたみ
- 検索履歴が0件の場合は表示しない

**実装コード:**
```typescript
'use client'

import { useState } from 'react'
import { SearchHistoryItem } from '@/types/agent'

export function SearchHistory({ items }: SearchHistoryProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (items.length === 0) {
    return null
  }

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-4 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded text-sm text-gray-600 cursor-pointer transition-colors"
      >
        <span className="flex items-center space-x-2">
          <span className="text-gray-400">{isExpanded ? '▼' : '▶'}</span>
          <span>実行した検索 ({items.length}件)</span>
        </span>
      </button>

      {isExpanded && (
        <div className="mt-2 px-4 py-3 bg-gray-50 border border-gray-200 rounded space-y-3">
          {items.map((item, idx) => (
            <SearchHistoryItemView key={idx} item={item} />
          ))}
        </div>
      )}
    </div>
  )
}

function SearchHistoryItemView({ item }: SearchHistoryItemViewProps) {
  return (
    <div className="space-y-1">
      <div className="font-medium text-gray-700 text-sm">{item.toolName}</div>
      {Object.keys(item.arguments).length > 0 && (
        <div className="text-xs text-gray-600">
          引数:{' '}
          {Object.entries(item.arguments)
            .map(([key, value]) => `${key}: ${JSON.stringify(value)}`)
            .join(', ')}
        </div>
      )}
      <div className="text-xs text-gray-700">{item.result}</div>
    </div>
  )
}
```

### 2.4 ChatMessageへの統合

**ファイル**: `frontend/src/components/chat/ChatMessage.tsx`

**変更点:**
1. `SearchHistoryItem`をインポート
2. `SearchHistory`コンポーネントをインポート
3. `ChatMessageProps`に`searchHistory`を追加
4. 回答の**上部**に`SearchHistory`を配置

```typescript
import { SearchHistoryItem } from '@/types/agent'
import { SearchHistory } from '../agent/SearchHistory'

interface ChatMessageProps {
  role: 'user' | 'assistant'
  content: string
  searchHistory?: SearchHistoryItem[]  // NEW
}

export function ChatMessage({
  role,
  content,
  searchHistory = [],  // NEW
}: ChatMessageProps) {
  // ...

  return (
    <div className="flex justify-start mb-6">
      <div className="max-w-[90%] ...">
        <SearchHistory items={searchHistory} />  {/* 回答の上に配置 */}
        <div dangerouslySetInnerHTML={{ __html: html as string }} />
      </div>
    </div>
  )
}
```

### 2.5 page.tsxのデータフロー統合

**ファイル**: `frontend/src/app/page.tsx`

**変更点:**
1. `SearchHistoryItem`をインポート
2. `Message`型に`searchHistory`フィールドを追加
3. `useAgentStream`から`searchHistory`を取得
4. `finalResponse`が来たら、`searchHistory`も一緒に`Message`に追加

```typescript
import { SearchHistoryItem } from '@/types/agent'

interface Message {
  role: 'user' | 'assistant'
  content: string
  searchHistory?: SearchHistoryItem[]  // NEW
}

function ChatPage() {
  const {
    events: agentEvents,
    currentMessage: agentCurrentMessage,
    finalResponse,
    searchHistory,  // NEW
    isLoading,
    error,
    sendQuery,
  } = useAgentStream()

  // 最終レスポンスが来たらメッセージに追加（検索履歴も含める）
  useEffect(() => {
    if (finalResponse) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: finalResponse,
          searchHistory: searchHistory,  // NEW
        },
      ])
    }
  }, [finalResponse, searchHistory])
}
```

### 2.6 ChatMessagesの型定義更新

**ファイル**: `frontend/src/components/chat/ChatMessages.tsx`

**変更点:**
1. `SearchHistoryItem`をインポート
2. `Message`型に`searchHistory`を追加
3. `ChatMessage`に`searchHistory`を渡す

```typescript
import { ProgressEvent, SearchHistoryItem } from '@/types/agent'

interface Message {
  role: 'user' | 'assistant'
  content: string
  searchHistory?: SearchHistoryItem[]  // NEW
}

export function ChatMessages({ messages, ... }: ChatMessagesProps) {
  return (
    <main className="flex-1 overflow-y-auto px-6 py-8">
      <div className="max-w-4xl mx-auto">
        {messages.map((message, idx) => (
          <ChatMessage
            key={idx}
            role={message.role}
            content={message.content}
            searchHistory={message.searchHistory}  // NEW
          />
        ))}
      </div>
    </main>
  )
}
```

### 2.7 進捗表示の色統一

**ファイル**: `frontend/src/components/agent/AgentProgress.tsx`

**変更点:**
検索中の進捗表示を、SearchHistoryと同じ薄いグレー色に変更

**Before (青色):**
```typescript
<div className="bg-blue-50 border border-blue-200 rounded-lg p-4 space-y-3">
  <div className="flex items-center space-x-2 text-blue-700">
    <Loader2 className="w-4 h-4 animate-spin" />
  </div>
  <div className="space-y-1.5 border-t border-blue-200 pt-3">
    <Loader2 className="w-3 h-3 text-blue-500 mt-0.5 flex-shrink-0 animate-spin" />
    <CheckCircle className="w-3 h-3 text-green-500 mt-0.5 flex-shrink-0" />
  </div>
</div>
```

**After (グレー色):**
```typescript
<div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
  <div className="flex items-center space-x-2 text-gray-700">
    <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
  </div>
  <div className="space-y-1.5 border-t border-gray-200 pt-3">
    <Loader2 className="w-3 h-3 text-gray-400 mt-0.5 flex-shrink-0 animate-spin" />
    <CheckCircle className="w-3 h-3 text-gray-500 mt-0.5 flex-shrink-0" />
  </div>
</div>
```

## 3. データフロー

```
1. ユーザーがクエリを送信
   ↓
2. useAgentStream.sendQuery() が SSE リクエストを送信
   ↓
3. バックエンドから ProgressEvent がストリーミングで返される
   ↓
4. function_call イベント → functionCallMap に保存
   ↓
5. function_result イベント → functionCallMap から取得して searchHistory に追加
   ↓
6. final_response イベント → finalResponse に保存
   ↓
7. page.tsx の useEffect で finalResponse を検知
   ↓
8. messages に { content, searchHistory } を追加
   ↓
9. ChatMessages → ChatMessage に searchHistory を渡す
   ↓
10. ChatMessage 内で SearchHistory コンポーネントを表示
```

## 4. 実装ファイル一覧

### 新規作成
- `frontend/src/components/agent/SearchHistory.tsx`

### 修正
1. `frontend/src/types/agent.ts`
   - `SearchHistoryItem` 型定義追加

2. `frontend/src/hooks/useAgentStream.ts`
   - `AgentStreamState` に `searchHistory` 追加
   - `functionCallMap` でペアを記録
   - `function_call` / `function_result` の処理追加

3. `frontend/src/components/chat/ChatMessage.tsx`
   - `searchHistory` props 追加
   - `SearchHistory` コンポーネント統合（回答の上に配置）

4. `frontend/src/app/page.tsx`
   - `Message` 型に `searchHistory` 追加
   - `useAgentStream` から `searchHistory` 取得
   - `finalResponse` と一緒に `searchHistory` を保存

5. `frontend/src/components/chat/ChatMessages.tsx`
   - `Message` 型に `searchHistory` 追加
   - `ChatMessage` に `searchHistory` を渡す

6. `frontend/src/components/agent/AgentProgress.tsx`
   - 青色 → グレー色に変更
   - `bg-blue-50` → `bg-gray-50`
   - `border-blue-200` → `border-gray-200`
   - `text-blue-700` → `text-gray-700`
   - `text-blue-500` → `text-gray-400`
   - `text-green-500` → `text-gray-500`

## 5. 動作確認

### 期待される動作
1. クエリを送信
2. 検索中の進捗が薄いグレーのボックスで表示される
3. 回答が表示される
4. 回答の**上部**に「▶ 実行した検索 (N件)」が薄いグレーで表示される
5. クリックすると「▼ 実行した検索 (N件)」に変わり、検索履歴が展開される
6. 各検索項目には:
   - ツール名（例: `search_customers`）
   - 引数（例: `industries: ["IT","通信"]`）
   - 結果（例: `3件の顧客が見つかりました`）

### テスト方法
```bash
# バックエンド起動
cd backend && source venv/bin/activate && python main.py

# フロントエンド起動
cd frontend && npm run dev

# ブラウザで http://localhost:3000 を開く
# クエリを送信して、検索履歴が表示されることを確認
```

## 6. 技術的なポイント

### Map を使った function_call/result のペアリング
- `function_call` と `function_result` は別々のイベントとして送られてくる
- `Map<toolName, arguments>` を使ってペアを記録
- `function_result` が来たら、`Map` から対応する `function_call` を取得してマージ

### 検索履歴の永続化
- `searchHistory` は `useAgentStream` の状態として保持
- `finalResponse` と一緒に `Message` に保存されるため、チャット履歴に残る
- ページをリロードしても（将来的にローカルストレージに保存すれば）履歴が残る

### アコーディオンの状態管理
- `SearchHistory` コンポーネント内で `useState` を使って展開/折りたたみ状態を管理
- デフォルトは折りたたみ（`isExpanded: false`）
- クリックで状態をトグル

## 7. 今後の拡張案

1. **検索結果の詳細データ表示**
   - 顧客リスト、ニュース記事などの詳細データを展開して表示

2. **検索履歴のエクスポート**
   - JSON/CSV形式でエクスポート機能

3. **検索履歴からの再実行**
   - 過去の検索を再実行する機能

4. **検索履歴のフィルタリング**
   - ツール名でフィルタ
   - 成功/失敗でフィルタ

5. **検索履歴の永続化**
   - ローカルストレージに保存
   - バックエンドに保存（ユーザーごとの履歴管理）

6. **デフォルトの展開状態をカスタマイズ**
   - ユーザー設定で展開/折りたたみのデフォルトを選択可能に

## 8. まとめ

検索履歴機能により、エージェントの内部動作がユーザーに可視化され、以下のメリットが得られる:

- **透明性の向上**: エージェントがどのような検索を行ったかが明確になる
- **デバッグの容易化**: 問題が発生した際に、どの検索で失敗したかを確認できる
- **信頼性の向上**: ユーザーはエージェントが適切な検索を行っていることを確認できる
- **学習効果**: ユーザーはエージェントの動作パターンを理解できる

Claude Code風のシンプルで薄いグレーのデザインにより、主要な回答を邪魔せず、必要な時だけ詳細を確認できるUIを実現した。
