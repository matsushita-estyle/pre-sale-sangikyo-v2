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


async def search_latest_news(keywords: list[str], days: int = 7) -> str:
    """Search latest news using Google Search Grounding.

    Args:
        keywords: List of keywords to search for
        days: Number of days to look back (default: 7)

    Returns:
        Formatted list of news articles
    """
    keyword_str = "、".join(keywords)

    try:
        # Gemini APIキーを取得
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.error("GEMINI_API_KEY not found")
            return "エラー: Gemini APIキーが設定されていません。"

        # Gemini clientを作成
        client = genai.Client(api_key=api_key)

        # Google Search Groundingを使用してニュース検索
        prompt = (
            f"「{keyword_str}」に関する最新ニュース（過去{days}日間）を検索し、"
            f"実際のニュース記事を3〜5件、日付と概要付きで教えてください。\n"
            f"各ニュースは以下の形式で出力してください:\n"
            f"- タイトル\n"
            f"  日付: YYYY-MM-DD\n"
            f"  概要: (100文字程度)\n"
        )

        config = types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.3,
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
            return f"{keyword_str} に関する最新ニュース:\n\n{response.text}"
        else:
            return f"{keyword_str} に関するニュースが見つかりませんでした。"

    except Exception as e:
        logger.error(f"Error in search_latest_news: {e}", exc_info=True)
        return f"ニュース検索中にエラーが発生しました: {str(e)}"


# ========================================
# Gemini Tool Declarations
# ========================================


search_latest_news_declaration = types.FunctionDeclaration(
    name="search_latest_news",
    description="指定されたキーワードで最新のニュースを検索します。",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "keywords": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="検索キーワードのリスト（例: ['KDDI', '5G']）",
            ),
            "days": types.Schema(
                type=types.Type.INTEGER,
                description="過去何日分のニュースを検索するか（デフォルト: 7日）",
            ),
        },
        required=["keywords"],
    ),
)
