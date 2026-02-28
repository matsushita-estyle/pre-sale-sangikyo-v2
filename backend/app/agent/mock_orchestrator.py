"""モックエージェントオーケストレーター（開発用）"""

import asyncio
from typing import AsyncIterator

from app.schemas.agent import ProgressEvent, ProgressEventType


class MockAgentOrchestrator:
    """モックエージェント（SSEの動作確認用）"""

    async def execute_query_stream(
        self, user_id: str, query: str
    ) -> AsyncIterator[ProgressEvent]:
        """
        モッククエリを実行し、進捗状況をストリームで返す

        Args:
            user_id: ユーザーID
            query: クエリ

        Yields:
            ProgressEvent: 進捗イベント
        """
        # ステップ1: ユーザー情報取得
        yield ProgressEvent(
            type=ProgressEventType.THINKING, message="ユーザー情報を取得中..."
        )
        await asyncio.sleep(1)

        # ステップ2: 顧客検索
        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_CALL,
            tool_name="search_customers",
            arguments={"industries": ["IT", "通信"]},
            message="顧客を検索中...",
        )
        await asyncio.sleep(1.5)

        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_RESULT,
            tool_name="search_customers",
            result="3件の顧客が見つかりました",
        )
        await asyncio.sleep(0.5)

        # ステップ3: ニュース取得
        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_CALL,
            tool_name="search_latest_news",
            arguments={"keywords": ["KDDI", "5G"]},
            message="最新ニュースを取得中...",
        )
        await asyncio.sleep(1.5)

        yield ProgressEvent(
            type=ProgressEventType.FUNCTION_RESULT,
            tool_name="search_latest_news",
            result="5件のニュースが見つかりました",
        )
        await asyncio.sleep(0.5)

        # ステップ4: レポート作成
        yield ProgressEvent(
            type=ProgressEventType.THINKING, message="レポートを作成中..."
        )
        await asyncio.sleep(2)

        # ステップ5: 最終レスポンス
        mock_response = """## 担当案件一覧

---

### KDDI株式会社
- 案件ID: 1
- **ステージ**: 商談
- **サービス種別**: 通信インフラ構築
- **金額**: ¥50,000,000

---

### ソフトバンク株式会社
- 案件ID: 2
- **ステージ**: 提案
- **サービス種別**: 技術人材派遣
- **金額**: ¥30,000,000

---

## 最新ニュース

- KDDI、5G基地局を西日本エリアに拡大
- ソフトバンク、ネットワークエンジニア採用強化
"""

        yield ProgressEvent(type=ProgressEventType.FINAL_RESPONSE, content=mock_response)
