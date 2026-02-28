# UI改善とコード品質向上

**日付:** 2026-03-01
**概要:** Markdownレンダリング、水平線表示、プロンプト管理、Ruffフォーマッター導入

---

## 1. Markdownレンダリングの改善

### 1.1 課題
AIの回答がMarkdown形式で生成されているが、フロントエンドで正しくレンダリングされていなかった。
- 見出し（`##`、`###`）が表示されない
- 箇条書きがプレーンテキストで表示
- 太字（`**`）が効いていない

### 1.2 解決策

#### バックエンド
プロンプトに明示的なMarkdownフォーマット指示を追加

**ファイル:** `backend/app/prompts/copilot_prompts.py`

```python
【出力形式】
回答は必ずMarkdown形式で出力してください。
- セクションごとに見出し（## または ###）を必ず付けてください
- 箇条書きは - を使用してください
- 重要な語句は **太字** で強調してください
- 企業名や案件情報は必ず見出しで区切ってください
```

#### フロントエンド
`marked`ライブラリでMarkdownをHTMLに変換し、Tailwindの`prose`クラスでスタイリング

**ファイル:** `frontend/src/components/chat/ChatMessage.tsx`

```typescript
import { marked } from 'marked'
import { useMemo } from 'react'

marked.setOptions({
  breaks: true, // 改行を<br>に変換
  gfm: true,    // GitHub Flavored Markdown
})

export function ChatMessage({ role, content }: ChatMessageProps) {
  const html = useMemo(() => {
    if (role === 'assistant') {
      return marked.parse(content) as string
    }
    return content
  }, [role, content])

  // ...
}
```

### 1.3 結果
- ✅ 見出し、箇条書き、太字が正しく表示される
- ✅ レスポンスが視覚的に読みやすくなった

---

## 2. 水平線（Horizontal Rule）の追加

### 2.1 目的
セクション間の区切りを視覚的に明確化し、情報の構造を分かりやすくする

### 2.2 実装

#### バックエンド
プロンプトに水平線（`---`）の使用を指示

**ファイル:** `backend/app/prompts/copilot_prompts.py`

```python
- セクション間には水平線（---）を入れて区切りを明確にしてください

例:
## 担当案件一覧

---

### KDDI株式会社
- 案件ID: 1
- **ステージ**: 商談

---

### ソフトバンク株式会社
- 案件ID: 2
- **ステージ**: 提案
```

#### フロントエンド
`prose-hr`クラスで水平線のスタイルを追加

**ファイル:** `frontend/src/components/chat/ChatMessage.tsx`

```typescript
<div className="prose prose-sm max-w-none
  prose-hr:my-6 prose-hr:border-t prose-hr:border-gray-300">
```

### 2.3 結果
- ✅ セクション間の区切りが視覚的に明確
- ✅ 複数案件の表示が読みやすくなった

---

## 3. スタイルのコンポーネントスコープ化

### 3.1 課題
当初、グローバルCSS（`globals.css`）でマークダウンスタイルを管理していた

```css
/* globals.css - 削除前 */
.markdown-content h2 {
  font-size: 1.5rem;
  font-weight: 600;
  /* ... */
}
```

**問題点:**
- グローバルな影響がある
- スタイルとコンポーネントロジックが分離
- 他のコンポーネントへの予期しない影響

### 3.2 解決策
Tailwindの任意バリアント構文（`[&_h2]:text-2xl`）およびproseモディファイアを使用してコンポーネント内でスタイルを完結

**ファイル:** `frontend/src/components/chat/ChatMessage.tsx`

```typescript
<div className="prose prose-sm max-w-none text-gray-800 leading-relaxed
  prose-headings:font-semibold prose-headings:text-gray-900
  prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg
  prose-p:my-3 prose-p:leading-7
  prose-ul:my-3 prose-ul:list-disc prose-ul:pl-6
  prose-ol:my-3 prose-ol:list-decimal prose-ol:pl-6
  prose-li:my-1 prose-li:leading-7
  prose-strong:font-semibold prose-strong:text-gray-900
  prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded
  prose-hr:my-6 prose-hr:border-t prose-hr:border-gray-300">
```

### 3.3 メリット
- ✅ グローバルな影響を回避
- ✅ スタイルとロジックが同じファイルで管理できる
- ✅ コンポーネントの独立性向上
- ✅ 他のコンポーネントへの影響なし

### 3.4 Tailwind CSS v4対応
**課題:** `@tailwindcss/typography`プラグインがTailwind v4と互換性がない

**解決策:** プラグインを使わず、`prose-*`モディファイアと任意バリアント構文でスタイリング

---

## 4. プロンプト管理の改善

### 4.1 課題
プロンプトがサービスコード内にハードコーディングされていた

**ファイル:** `backend/app/services/copilot_service.py` (修正前)

```python
async def chat(self, user_id: str, query: str) -> str:
    # ...
    prompt = f"""あなたは営業支援AIアシスタントです。
以下のデータを参考に、ユーザーの質問に日本語で丁寧に回答してください。
{user_context}
【質問】
{query}
...（長いプロンプト文）
"""
```

**問題点:**
- プロンプトとビジネスロジックが混在
- プロンプトの再利用が困難
- バージョン管理が不明瞭

### 4.2 解決策
`app/prompts/`ディレクトリを作成し、プロンプトを関数として分離

#### ディレクトリ構造
```
backend/app/
├── prompts/
│   ├── __init__.py
│   └── copilot_prompts.py  # ★ 新規作成
```

#### プロンプトファイル
**ファイル:** `backend/app/prompts/copilot_prompts.py`

```python
"""Prompts for the copilot chat service."""

def build_chat_prompt(user_context: str, query: str) -> str:
    """
    Build the chat prompt for Gemini API.

    Args:
        user_context: User's context data (deals, customers, etc.)
        query: User's question

    Returns:
        Formatted prompt string
    """
    return f"""あなたは営業支援AIアシスタントです。
以下のデータを参考に、ユーザーの質問に日本語で丁寧に回答してください。

{user_context}

【質問】
{query}

【回答のガイドライン】
- 上記のデータに基づいて具体的に回答してください
- データにない情報を推測で補わないでください
- 営業活動に役立つ実用的なアドバイスを提供してください

【出力形式】
回答は必ずMarkdown形式で出力してください。
- セクションごとに見出し（## または ###）を必ず付けてください
- 箇条書きは - を使用してください
- 重要な語句は **太字** で強調してください
- 企業名や案件情報は必ず見出しで区切ってください
- セクション間には水平線（---）を入れて区切りを明確にしてください

例:
## 担当案件一覧

---

### KDDI株式会社
- 案件ID: 1
- **ステージ**: 商談

---

### ソフトバンク株式会社
- 案件ID: 2
- **ステージ**: 提案
"""
```

#### サービス層の修正
**ファイル:** `backend/app/services/copilot_service.py`

```python
from app.prompts.copilot_prompts import build_chat_prompt

async def chat(self, user_id: str, query: str) -> str:
    # ...
    user_context = await self._get_user_context(user_id)

    # Build prompt with context
    prompt = build_chat_prompt(user_context, query)

    # Generate response
    response = self.client.models.generate_content(model=self.model_id, contents=prompt)
```

### 4.3 メリット
- ✅ プロンプトの再利用性向上
- ✅ プロンプトのバージョン管理が容易
- ✅ サービスロジックとプロンプトが分離され、可読性向上
- ✅ 複数のプロンプトを追加しやすい
- ✅ プロンプトエンジニアリングがしやすい

---

## 5. Ruffフォーマッターの導入

### 5.1 目的
バックエンドコードの一貫性を保ち、フロントエンドのPrettierと同様にコード品質を向上

### 5.2 Ruffとは
- **Rustで実装**された高速なPythonリンター＆フォーマッター
- Black/Flake8より**10〜100倍高速**
- リンター + フォーマッター + import整理が**1つのツールで完結**
- 2023年以降急速に普及、FastAPI/Pydantic等の主要プロジェクトが採用

### 5.3 導入手順

#### 依存関係の追加
**ファイル:** `backend/requirements.txt`

```
ruff>=0.8.0
```

```bash
pip install ruff
```

#### 設定ファイルの作成
**ファイル:** `backend/ruff.toml`

```toml
# Python version
target-version = "py311"

# Line length
line-length = 100

[lint]
# Enable specific rule sets
select = [
    "E",     # pycodestyle errors
    "W",     # pycodestyle warnings
    "F",     # pyflakes
    "I",     # isort (import sorting)
    "N",     # pep8-naming
    "UP",    # pyupgrade
    "B",     # flake8-bugbear
    "C4",    # flake8-comprehensions
    "SIM",   # flake8-simplify
]

# Ignore specific rules
ignore = [
    "E501",  # line too long (handled by formatter)
    "B008",  # function call in argument defaults (FastAPI Depends pattern)
    "B904",  # raise from inside except (not always necessary)
    "N818",  # exception naming (allow AppException)
]

[format]
# Use double quotes for strings
quote-style = "double"

# Indent with spaces
indent-style = "space"
```

**設定のポイント:**
- `B008`: FastAPIの`Depends()`パターンを許可
- `B904`: 例外チェーン（`raise ... from err`）を強制しない
- `N818`: 例外クラス名の命名規則を緩和（`AppException`を許可）

### 5.4 実行結果

```bash
# リンティング + 自動修正
$ ruff check . --fix
Found 91 errors (73 fixed, 18 remaining).

# フォーマット
$ ruff format .
13 files reformatted, 7 files left unchanged

# 最終確認
$ ruff check .
All checks passed!
```

**修正内容:**
- ✅ 73個のコードスタイル問題を自動修正
- ✅ 13ファイルをフォーマット
- ✅ 全リンティングチェックをパス

### 5.5 使い方

```bash
# リンティング
ruff check .

# 自動修正
ruff check . --fix

# フォーマット
ruff format .
```

### 5.6 メリット
- ✅ コードの一貫性が保たれる
- ✅ フロントエンド（Prettier）と同様のワークフロー
- ✅ 高速（大規模プロジェクトでも瞬時）
- ✅ 1つのツールでリンター＋フォーマッター＋import整理

---

## 6. 技術的な詳細

### 6.1 markedライブラリの設定

```typescript
marked.setOptions({
  breaks: true,  // 改行を<br>に変換（GFM準拠）
  gfm: true,     // GitHub Flavored Markdown有効化
})
```

### 6.2 プロンプトエンジニアリングのポイント

1. **明示的な指示:** 「Markdown形式で出力」と明示
2. **具体例の提示:** 期待する出力フォーマットを例示
3. **構造化:** セクションごとに見出しを必須化
4. **視覚的区切り:** 水平線で情報を整理

### 6.3 Tailwind CSS v4での対応

**課題:** `@tailwindcss/typography`プラグインが非対応

**解決策:**
- `prose`クラス + モディファイア（`prose-h2:text-xl`）を使用
- 任意バリアント構文（`[&_h2]:...`）も併用可能

---

## 7. まとめ

### 7.1 実装した改善
1. ✅ Markdownレンダリングの実装（見出し、箇条書き、太字）
2. ✅ 水平線による視覚的な区切り
3. ✅ コンポーネントスコープのスタイリング
4. ✅ プロンプト管理の改善（`app/prompts/`ディレクトリ）
5. ✅ Ruffフォーマッターの導入

### 7.2 変更ファイル一覧
- `backend/app/prompts/copilot_prompts.py` - 新規作成
- `backend/app/prompts/__init__.py` - 新規作成
- `backend/app/services/copilot_service.py` - プロンプトインポート
- `backend/requirements.txt` - Ruff追加
- `backend/ruff.toml` - 新規作成
- `frontend/src/components/chat/ChatMessage.tsx` - Markdownレンダリング
- `frontend/src/app/globals.css` - グローバルスタイル削除

### 7.3 成果
- **UI/UX:** 視覚的に読みやすいチャット画面
- **保守性:** プロンプトが管理しやすくなった
- **コード品質:** Ruffによる一貫したコードスタイル
- **開発効率:** フォーマッター自動修正により手作業削減

---

## 8. 次のステップ

### 優先度: 高
1. **認証機能の実装:** Azure AD B2Cを使ったユーザー認証
2. **エラーハンドリング強化:** より詳細なエラーメッセージとリトライロジック

### 優先度: 中
3. **テストの追加:** pytest（バックエンド）、Jest（フロントエンド）
4. **ストリーミングレスポンス:** Gemini APIのストリーミングを活用
5. **CI/CD:** GitHub Actionsで自動テスト・デプロイ

### 優先度: 低
6. **UI/UX改善:** ダークモード対応
7. **パフォーマンス最適化:** フロントエンドのコード分割
8. **国際化:** 多言語対応（i18n）
