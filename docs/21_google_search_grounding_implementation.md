# Google Search Grounding 実装計画

**作成日**: 2026-03-01
**ステータス**: 計画中

## 概要

現在、`search_latest_news` ツールはモックデータを返すだけで、実際のWeb検索を行っていません。
Gemini 2.0 の Google Search Grounding 機能を使って、実際のニュース検索を実装します。

## 現状の問題

### 現在のモック実装

**ファイル**: `backend/app/agent/tools.py` (223-250行目)

```python
async def search_latest_news(keywords: list[str], days: int = 7) -> str:
    # TODO: 実際のニュースAPIに置き換える
    keyword_str = "、".join(keywords)

    mock_news = [
        {
            "title": f"{keywords[0]}、次世代通信インフラに1000億円投資",
            "date": "2026-02-28",
            "summary": "...",
        },
        # ... モックデータ
    ]
```

**問題点**:
- 実際のニュースを取得できない
- 常に同じ架空のニュースを返す
- 日付や内容がユーザーの質問と関係ない

## 実装方針

### 選択肢の比較

| 方法 | メリット | デメリット | 推奨度 |
|------|---------|-----------|--------|
| **Google Search Grounding** | • Gemini組み込み機能<br>• 実装が簡単<br>• 高品質な結果<br>• 追加費用不要 | • Gemini APIに依存 | ⭐⭐⭐⭐⭐ |
| Google Custom Search API | • 柔軟性が高い<br>• カスタマイズ可能 | • 別途API設定が必要<br>• 有料（1000クエリ/日以降） | ⭐⭐⭐ |
| NewsAPI.org | • ニュース専門<br>• フィルタリング豊富 | • 有料プラン必要<br>• 追加の統合作業 | ⭐⭐ |

**採用方針**: **Google Search Grounding** を使用

### Google Search Grounding とは

Gemini 2.0 に組み込まれたGoogle検索機能で、以下の特徴があります:

1. **リアルタイム情報取得**: 最新のWeb情報にアクセス可能
2. **信頼性の高い情報源**: Google検索の品質を活用
3. **簡単な実装**: `google_search` ツールを有効化するだけ
4. **統合された回答**: 検索結果を自然にLLMの回答に統合

## 実装計画

### Phase 1: Google Search Grounding の調査と検証

**目的**: Gemini APIでGoogle Search Groundingが使用可能か確認

**タスク**:
1. Gemini 2.0 Flash の Google Search Grounding 機能を調査
2. APIドキュメントを確認
3. 簡単なテストコードで動作確認

**成果物**:
- 動作確認スクリプト
- 使用可能な機能の一覧

### Phase 2: search_latest_news ツールの再実装

**目的**: モック実装を実際のGoogle検索に置き換え

**変更ファイル**:
- `backend/app/agent/tools.py`
- `backend/app/agent/orchestrator.py`

**実装内容**:

#### オプション A: Google Search Grounding をツールとして使用

Gemini に組み込みの `google_search` ツールを有効化:

```python
# orchestrator.py
from google.genai import types

# Google Search ツールを追加
def _get_grounding_tools(self) -> list[types.Tool]:
    return [
        types.Tool(google_search=types.GoogleSearch())
    ]

# generate_content 時に追加
config = types.GenerateContentConfig(
    systemInstruction=self.system_instruction,
    tools=self.tools + self._get_grounding_tools(),  # Google Search追加
    temperature=0.7,
)
```

#### オプション B: search_latest_news 内でGeminiを呼び出し

既存のツールを維持しつつ、内部でGoogle検索:

```python
# tools.py
async def search_latest_news(keywords: list[str], days: int = 7) -> str:
    """Search latest news using Google Search Grounding."""

    # キーワードをクエリに変換
    query = f"{' '.join(keywords)} ニュース 過去{days}日"

    # Gemini + Google Search で検索
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.3,
    )

    response = await asyncio.to_thread(
        client.models.generate_content,
        model="gemini-2.0-flash",
        contents=f"次のキーワードに関する最新のニュースを3-5件、日付と概要付きで教えてください: {query}",
        config=config,
    )

    # レスポンスをフォーマット
    return response.text
```

**推奨**: **オプション A**
- エージェント自身がGoogle検索を直接使用できる
- より柔軟な情報収集が可能
- ニュース以外の情報も検索可能

### Phase 3: ツール定義の更新

**変更箇所**: `backend/app/agent/tools.py` の `get_tools()`

**オプション A の場合**:
- `search_latest_news` ツールは削除または簡素化
- Google Search はGeminiが直接使用

**オプション B の場合**:
- `search_latest_news` のdescriptionを更新
- パラメータは既存のまま維持

### Phase 4: システムプロンプトの更新

**変更箇所**: `backend/app/agent/orchestrator.py` の `_get_system_instruction()`

**追加内容**:

```python
利用可能なツール:
- get_user_info: ユーザー情報を取得
- search_customers: 顧客を検索
- get_customer_details: 顧客詳細を取得
- search_deals: 案件を検索
- get_deal_details: 案件詳細を取得
- google_search: Webから最新情報を検索（ニュース、企業情報、技術動向など）

google_search の使い方:
- ユーザーがニュースや最新情報を求めている場合に使用
- 具体的なキーワードで検索する
- 検索結果を簡潔にまとめて回答に含める
```

### Phase 5: テストとデバッグ

**テストケース**:

1. **基本的なニュース検索**
   - 質問: "KDDIの最新ニュースを教えて"
   - 期待: 実際のKDDI関連ニュースを返す

2. **複数キーワード**
   - 質問: "ソフトバンクの5G関連のニュースは？"
   - 期待: ソフトバンク + 5G でフィルタされたニュース

3. **期間指定**
   - 質問: "過去3日のNTTドコモのニュースを教えて"
   - 期待: 過去3日間のニュースのみ

4. **エージェント連携**
   - 質問: "私の担当顧客の最新ニュースを教えて"
   - 期待:
     1. search_deals で担当案件を取得
     2. 顧客名を抽出
     3. google_search で各顧客のニュースを検索
     4. 統合して回答

**確認項目**:
- [ ] Google Search が正常に動作する
- [ ] 検索結果が適切にフォーマットされる
- [ ] エラーハンドリングが適切
- [ ] レスポンス時間が許容範囲内（10秒以内）
- [ ] 検索結果が日本語で返される

### Phase 6: ドキュメント更新

**更新ファイル**:
- `docs/20_gemini_function_calling_agent_design.md` - ツール一覧を更新
- `README.md` - Google Search Grounding の説明を追加

## 実装スケジュール

| Phase | タスク | 所要時間 | 担当 |
|-------|--------|---------|------|
| Phase 1 | Google Search Grounding 調査 | 30分 | 開発者 |
| Phase 2 | search_latest_news 再実装 | 1時間 | 開発者 |
| Phase 3 | ツール定義更新 | 15分 | 開発者 |
| Phase 4 | システムプロンプト更新 | 15分 | 開発者 |
| Phase 5 | テスト・デバッグ | 1時間 | 開発者 |
| Phase 6 | ドキュメント更新 | 30分 | 開発者 |

**合計**: 約3.5時間

## 技術的考慮事項

### レート制限

- Gemini APIのレート制限内で動作するか確認
- 必要に応じてキャッシュ機構を追加

### エラーハンドリング

```python
try:
    # Google Search実行
    response = await search_with_grounding(query)
except Exception as e:
    logger.error(f"Google Search failed: {e}")
    return "申し訳ございません。ニュース検索中にエラーが発生しました。"
```

### コスト管理

- Google Search Grounding は Gemini API の一部として課金
- 使用量を監視し、必要に応じて制限を設定

### セキュリティ

- ユーザー入力のサニタイゼーション
- 検索結果の安全性確認

## リスクと対策

| リスク | 影響度 | 対策 |
|--------|--------|------|
| Google Search Grounding が利用不可 | 高 | 代替API（NewsAPI）を準備 |
| レスポンスが遅い | 中 | タイムアウト設定、キャッシュ実装 |
| 検索結果の品質が低い | 中 | クエリの最適化、フィルタリング強化 |
| コストが高い | 低 | 使用量制限、キャッシュ活用 |

## 成功基準

- [ ] 実際のWeb検索結果が取得できる
- [ ] レスポンス時間が10秒以内
- [ ] 検索結果が日本語で適切にフォーマットされる
- [ ] エージェントが複数ツールと連携して動作する
- [ ] エラーが発生しても適切にハンドリングされる

## 参考資料

- [Gemini API - Grounding with Google Search](https://ai.google.dev/gemini-api/docs/grounding)
- [Google Search Grounding 公式ドキュメント](https://cloud.google.com/vertex-ai/generative-ai/docs/grounding/overview)
- [Function Calling + Grounding 統合例](https://ai.google.dev/gemini-api/docs/function-calling)

## 次のステップ

1. Phase 1 の調査を開始
2. 動作確認後、実装方針（オプションA vs B）を最終決定
3. Phase 2 以降を順次実装
