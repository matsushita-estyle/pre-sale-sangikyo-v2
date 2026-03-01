# 会話履歴一覧表示UI実装計画（修正版）

## 概要
ユーザーが過去の会話履歴を一覧表示し、選択して再開できる機能を実装する。

## 現状
- ✅ Backend: `GET /api/v1/users/{user_id}/conversations` API実装済み
- ✅ Frontend: `lib/api.ts`にAPI関数実装済み
- ✅ 会話履歴の保存・取得機能は完成
- ✅ `store/conversationStore.ts`作成済み
- ⏳ UI実装が未着手

## UI設計

### レイアウト
```
サイドバー（既存Sidebarコンポーネント内）
├─ SFA Agent
├─ チャット
├─ データ管理
├─────────────────── ← 区切り線（新規）
│ 会話履歴           ← 常時表示（新規）
├─ + 新規会話
├─ 📝 KDDIの案件について
├─ 📝 営業戦略の相談
├─ 📝 顧客リスト確認
└─ [ユーザー選択]
```

### コンポーネント構成

1. **ConversationList** (新規)
   - サイドバー内に組み込む会話履歴セクション
   - 新規会話ボタン
   - 会話リスト（スクロール可能）
   - データ管理メニューと区切り線で分離

2. **ConversationListItem** (新規)
   - 個別の会話アイテム
   - タイトル表示（最初のメッセージから生成）
   - 最終更新日時
   - 選択状態のハイライト

3. **Sidebar.tsx** (変更)
   - ナビゲーションメニューの下に区切り線を追加
   - ConversationListコンポーネントを挿入
   - スクロール可能なレイアウトに調整

4. **page.tsx** (変更)
   - 会話選択時の動作を追加
   - 新規会話作成時の動作を追加
   - 会話履歴のロードとメッセージ復元

## 状態管理

### Store: `conversationStore.ts` ✅
```typescript
interface ConversationStore {
  conversations: Conversation[]
  selectedConversationId: string | null
  isLoading: boolean
  error: string | null

  // Actions
  fetchConversations: (userId: string) => Promise<void>
  selectConversation: (conversationId: string | null) => void
  startNewConversation: () => void
}
```

## 実装フェーズ

### Phase 1: Store作成 ✅
- ✅ `store/conversationStore.ts`を作成
- ✅ Zustandで会話一覧の状態管理
- ✅ API連携機能

### Phase 2: コンポーネント作成
- [ ] `components/conversation/ConversationList.tsx`
  - 新規会話ボタン
  - 会話リスト（スクロール可能）
  - 「会話履歴」ラベル
- [ ] `components/conversation/ConversationListItem.tsx`
  - タイトル表示
  - 日時表示
  - 選択状態のスタイリング

### Phase 3: Sidebar統合
- [ ] `components/layout/Sidebar.tsx`を変更
  - ナビゲーションの下に区切り線を追加
  - ConversationListコンポーネントを組み込み
  - スクロール領域の調整（会話リスト部分のみスクロール可能に）

### Phase 4: page.tsx統合
- [ ] 会話選択時の処理
  - `getConversation(conversationId)`でメッセージ履歴を取得
  - `setMessages()`でチャット画面に反映
  - `conversationId`をuseAgentStreamに設定
- [ ] 新規会話作成処理
  - メッセージクリア
  - conversationIdをnullに
  - 次のメッセージ送信時に新規会話を作成
- [ ] 初回レンダリング時に会話履歴を取得
- [ ] メッセージ送信後に会話履歴を再取得

### Phase 5: UX改善（オプション）
- [ ] 会話タイトルの自動生成（最初のメッセージから）
- [ ] ローディング状態表示
- [ ] エラーハンドリング
- [ ] 会話削除機能

## 技術的考慮事項

### 会話の取得タイミング
- 初回レンダリング時に`fetchConversations(userId)`を実行
- 新規メッセージ送信後に再取得（リアルタイム更新）

### 会話の選択処理
1. ConversationListItemクリック
2. `selectConversation(conversationId)`を実行
3. `getConversation(conversationId)`でメッセージ履歴を取得
4. `setMessages()`でチャット画面に反映
5. `conversationId`をuseAgentStreamに設定

### 新規会話の作成
1. 「新規会話」ボタンクリック
2. `startNewConversation()`を実行
3. メッセージをクリア
4. conversationIdをnullに設定
5. 次のメッセージ送信時にバックエンドが新規会話を作成

### レイアウト調整
- Sidebar全体の高さを`h-screen`で固定
- ナビゲーションエリア: 固定
- 会話履歴リストエリア: スクロール可能（`overflow-y-auto`）
- ユーザー選択: 固定（下部）

## ファイル一覧

### 新規作成
- ✅ `frontend/src/store/conversationStore.ts`
- [ ] `frontend/src/components/conversation/ConversationList.tsx`
- [ ] `frontend/src/components/conversation/ConversationListItem.tsx`

### 変更
- [ ] `frontend/src/components/layout/Sidebar.tsx` - ConversationList組み込み
- [ ] `frontend/src/app/page.tsx` - 会話選択・復元ロジック

## 見積もり
- Phase 1: ✅ 完了
- Phase 2: 1時間
- Phase 3: 30分
- Phase 4: 1時間
- Phase 5: 1時間（オプション）

**合計**: 約2.5〜3.5時間
