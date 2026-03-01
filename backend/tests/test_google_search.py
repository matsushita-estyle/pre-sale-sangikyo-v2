"""Test script for Google Search Grounding."""

import asyncio
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()


async def test_google_search():
    """Test Google Search Grounding with Gemini."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY not found")
        return

    client = genai.Client(api_key=api_key)

    # Google Search Grounding を有効化
    config = types.GenerateContentConfig(
        tools=[types.Tool(google_search=types.GoogleSearch())],
        temperature=0.3,
    )

    print("🔍 Testing Google Search Grounding...")
    print("Query: 'KDDI 2026年 最新ニュース'\n")

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents="KDDIの2026年の最新ニュースを3つ教えてください。日付と概要も含めてください。",
            config=config,
        )

        print("✅ Success!\n")
        print("=" * 60)
        print(response.text)
        print("=" * 60)

        # Grounding metadata を確認
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "grounding_metadata"):
                print("\n📊 Grounding Metadata:")
                print(candidate.grounding_metadata)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_google_search())
