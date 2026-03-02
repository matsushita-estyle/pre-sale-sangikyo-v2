"""News-related tools for Gemini Function Calling Agent."""

import asyncio
import logging
import os

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


# ========================================
# Tool Functions
# ========================================


async def search_latest_news(
    company_name: str, keywords: list[str] | None = None
) -> str:
    """Search latest news for a specific company using Google Search Grounding.

    Args:
        company_name: Name of the company to search news for
        keywords: Optional additional keywords to refine the search

    Returns:
        Formatted list of news articles
    """
    try:
        # Gemini APIキーを取得
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found")
            return "エラー: Gemini APIキーが設定されていません。"

        # Gemini clientを作成
        client = genai.Client(api_key=api_key)

        # 検索クエリの構築
        search_query = f"{company_name} 最新ニュース"
        if keywords:
            search_query += " " + " ".join(keywords)

        # 現在の年を取得
        from datetime import datetime
        current_year = datetime.now().year

        # Google Search Groundingを使用してニュース検索
        prompt = (
            f"「{company_name}」の最新ニュース（{current_year}年）を検索し、"
            f"実在するニュース記事を3〜5件、以下の形式で教えてください。\n\n"
            f"検索クエリ: {search_query}\n\n"
            f"各ニュースは以下の形式で出力してください:\n"
            f"1. **タイトル**: [ニュースタイトル]\n"
            f"   - 日付: YYYY-MM-DD\n"
            f"   - 概要: [100文字程度の要約]\n"
            f"   - ソース: [情報源]\n"
        )

        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.1,
        )

        # 非同期実行
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents=prompt,
            config=config,
        )

        # レスポンステキストを取得
        if response.text:
            return f"{company_name}の最新ニュース:\n\n{response.text}"
        else:
            return f"{company_name}に関するニュースが見つかりませんでした。"

    except Exception as e:
        logger.error(f"Error in search_latest_news: {e}", exc_info=True)
        return f"ニュース検索中にエラーが発生しました: {str(e)}"


# ========================================
# Gemini Tool Declarations
# ========================================


search_latest_news_declaration = types.FunctionDeclaration(
    name="search_latest_news",
    description="企業の最新ニュースを検索します（Google Search使用）。各企業ごとに1回ずつ呼び出してください。",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "company_name": types.Schema(
                type=types.Type.STRING,
                description="企業名（例: 'KDDI株式会社', 'ソフトバンク'）",
            ),
            "keywords": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="追加の検索キーワード（任意。例: ['5G', 'データセンター']）",
            ),
        },
        required=["company_name"],
    ),
)
