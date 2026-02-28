"""Copilot service for AI chat functionality."""

import logging
import os

from google import genai

from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository
from app.prompts.copilot_prompts import build_chat_prompt

logger = logging.getLogger(__name__)


class CopilotService:
    """Service for handling AI chat using Gemini API."""

    def __init__(
        self,
        deal_repo: DealRepository | None = None,
        customer_repo: CustomerRepository | None = None,
    ):
        """Initialize Gemini API."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")

        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-2.0-flash"

        # Initialize repositories
        self.deal_repo = deal_repo or DealRepository()
        self.customer_repo = customer_repo or CustomerRepository()

        logger.info(f"Gemini API initialized with model: {self.model_id}")

    async def _get_user_context(self, user_id: str) -> str:
        """
        Gather user's context data from Cosmos DB.

        Args:
            user_id: User ID

        Returns:
            Formatted context string
        """
        try:
            # Get user's deals
            deals = await self.deal_repo.get_deals_by_user(user_id)

            if not deals:
                return "現在、あなたの担当案件はありません。"

            # Format deals information
            context_parts = ["【あなたの担当案件】"]
            for deal in deals:
                deal_info = f"""
- 顧客: {deal.customer_name or "不明"}
  案件ID: {deal.deal_id}
  ステージ: {deal.deal_stage}
  サービス種別: {deal.service_type or "未設定"}
  金額: {f"¥{int(deal.deal_amount):,}" if deal.deal_amount else "未設定"}
  最終接触日: {deal.last_contact_date or "未記録"}
  メモ: {deal.notes or "なし"}"""
                context_parts.append(deal_info)

            return "\n".join(context_parts)

        except Exception as e:
            logger.error(f"Error gathering user context: {e}", exc_info=True)
            return "データ取得中にエラーが発生しました。"

    async def chat(self, user_id: str, query: str) -> str:
        """
        Process a chat query using Gemini API with RAG.

        Args:
            user_id: User ID
            query: User's question

        Returns:
            AI-generated response
        """
        try:
            logger.info(f"Processing chat query for user {user_id}: {query[:50]}...")

            # Step 2: Get user context from Cosmos DB
            user_context = await self._get_user_context(user_id)
            logger.info(f"Retrieved context for user {user_id}")

            # Build prompt with context
            prompt = build_chat_prompt(user_context, query)

            # Generate response
            response = self.client.models.generate_content(model=self.model_id, contents=prompt)

            if not response.text:
                logger.warning("Empty response from Gemini API")
                return "申し訳ございません。回答を生成できませんでした。"

            logger.info(f"Generated response: {response.text[:100]}...")
            return response.text

        except Exception as e:
            logger.error(f"Error in chat service: {e}", exc_info=True)
            raise


# Singleton instance
_copilot_service: CopilotService | None = None


def get_copilot_service() -> CopilotService:
    """Get or create CopilotService singleton instance."""
    global _copilot_service
    if _copilot_service is None:
        _copilot_service = CopilotService()
    return _copilot_service
