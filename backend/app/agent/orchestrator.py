"""Gemini Function Calling Agent Orchestrator."""

import asyncio
import logging
import os
from typing import AsyncIterator

from google import genai
from google.genai import types

from app.agent.tools import execute_tool, get_tools
from app.schemas.agent import ProgressEvent, ProgressEventType

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Gemini Function Calling Agent Orchestrator."""

    def __init__(self):
        """Initialize agent with Gemini model."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")

        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"
        self.tools = get_tools()
        self.system_instruction = self._get_system_instruction()

    def _get_system_instruction(self) -> str:
        """Get system instruction for the agent.

        Returns:
            System instruction string
        """
        return """あなたは営業支援AIアシスタントです。
営業担当者の案件管理、顧客情報検索、最新ニュース収集をサポートします。

利用可能なツール:
- get_user_info: ユーザー情報を取得
- search_customers: 顧客を検索
- get_customer_details: 顧客詳細を取得
- search_deals: 案件を検索
- get_deal_details: 案件詳細を取得
- search_latest_news: 最新ニュースを検索

ツール使用時のガイドライン:
1. search_dealsのdeal_stageパラメータ:
   - ユーザーが特定のステージを指定していない場合は、パラメータを省略して全件検索する
   - 「私の案件」「担当案件」などの質問では、deal_stageを指定せずにsales_user_idのみで検索する
   - ステージの指定がある場合のみdeal_stageを使用する（例：「商談中の案件」「失注した案件」）

2. search_customersのkeywordパラメータ:
   - ユーザーが明示的にキーワードを指定していない場合は、パラメータを省略して全件検索する
   - 「顧客一覧」「全ての顧客」などの質問では、keywordを省略する

3. ユーザーに追加情報を聞き返すのは、必須パラメータが不明な場合のみにする
   - オプションパラメータが不明な場合は、省略して実行する
   - 不要な確認質問は避け、すぐにツールを実行する

回答時のガイドライン:
1. 必要なツールを適切に使用して情報を収集する
2. 簡潔で分かりやすい回答を心がける
3. Markdown形式で構造化された回答を返す
4. 数値やデータは正確に伝える
5. ユーザーの質問に直接答える
6. 「私」という一人称を使ってユーザーに話しかける場合、ユーザー自身の情報を指す
"""

    async def execute_query_stream(
        self, user_id: str, query: str
    ) -> AsyncIterator[ProgressEvent]:
        """Execute query with function calling and stream progress.

        Args:
            user_id: User ID making the query
            query: User's query string

        Yields:
            ProgressEvent objects representing the agent's progress
        """
        # 初期メッセージ
        yield ProgressEvent(
            type=ProgressEventType.THINKING, message="クエリを解析中..."
        )

        # チャット履歴の初期化（ユーザーコンテキストを含める）
        initial_context = f"現在のユーザーID: {user_id}\n\nユーザーからの質問: {query}"
        chat_history = [{"role": "user", "parts": [{"text": initial_context}]}]

        # Function Calling ループ
        max_iterations = 10
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.info(f"Function calling iteration {iteration}/{max_iterations}")

            try:
                # Geminiにリクエスト送信（同期APIを非同期ラッパーで実行）
                config = types.GenerateContentConfig(
                    systemInstruction=self.system_instruction,
                    tools=self.tools,
                    temperature=0.7,
                )

                response = await asyncio.to_thread(
                    self.client.models.generate_content,
                    model=self.model_id,
                    contents=chat_history,
                    config=config,
                )

                # レスポンスの解析
                if not response.candidates:
                    yield ProgressEvent(
                        type=ProgressEventType.ERROR,
                        message="レスポンスを生成できませんでした。",
                    )
                    return

                candidate = response.candidates[0]

                # Function Call があるか確認
                has_function_calls = False
                if candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call is not None:
                            has_function_calls = True
                            break

                if has_function_calls:
                    # Function Call を実行
                    function_responses = []

                    for part in candidate.content.parts:
                        if hasattr(part, "function_call") and part.function_call is not None:
                            fc = part.function_call

                            # Function Call イベントを送信
                            yield ProgressEvent(
                                type=ProgressEventType.FUNCTION_CALL,
                                tool_name=fc.name,
                                arguments=dict(fc.args) if fc.args else {},
                                message=f"{fc.name}を実行中...",
                            )

                            # ツールを実行
                            try:
                                result = await execute_tool(
                                    fc.name, dict(fc.args) if fc.args else {}
                                )

                                logger.info(
                                    f"Tool {fc.name} executed successfully. Result length: {len(result)}"
                                )

                                # Function Result イベントを送信
                                yield ProgressEvent(
                                    type=ProgressEventType.FUNCTION_RESULT,
                                    tool_name=fc.name,
                                    result=f"{fc.name}の実行が完了しました",
                                )

                                # Function Response を作成
                                function_responses.append(
                                    types.Part.from_function_response(
                                        name=fc.name, response={"result": result}
                                    )
                                )

                            except Exception as e:
                                logger.error(
                                    f"Error executing tool {fc.name}: {e}",
                                    exc_info=True,
                                )
                                yield ProgressEvent(
                                    type=ProgressEventType.ERROR,
                                    message=f"{fc.name}の実行中にエラーが発生しました: {str(e)}",
                                )
                                return

                    # チャット履歴にFunction Callとその結果を追加
                    chat_history.append(
                        {"role": "model", "parts": candidate.content.parts}
                    )
                    chat_history.append({"role": "user", "parts": function_responses})

                else:
                    # テキストレスポンスがある場合は終了
                    if candidate.content.parts:
                        text_parts = [
                            part.text
                            for part in candidate.content.parts
                            if hasattr(part, "text")
                        ]
                        if text_parts:
                            final_response = "".join(text_parts)

                            logger.info(
                                f"Final response generated. Length: {len(final_response)}"
                            )

                            yield ProgressEvent(
                                type=ProgressEventType.FINAL_RESPONSE,
                                content=final_response,
                            )
                            return

                    # それ以外の場合はエラー
                    yield ProgressEvent(
                        type=ProgressEventType.ERROR,
                        message="予期しないレスポンス形式です。",
                    )
                    return

            except Exception as e:
                logger.error(
                    f"Error in function calling loop (iteration {iteration}): {e}",
                    exc_info=True,
                )
                yield ProgressEvent(
                    type=ProgressEventType.ERROR,
                    message=f"エラーが発生しました: {str(e)}",
                )
                return

        # 最大反復回数に達した場合
        logger.warning(f"Max iterations ({max_iterations}) reached")
        yield ProgressEvent(
            type=ProgressEventType.ERROR,
            message="最大反復回数に達しました。質問を簡潔にしてお試しください。",
        )
