"""Repository for conversation history."""

import logging
import uuid
from datetime import datetime

from app.models.conversation import Conversation, Message
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository):
    """Repository for managing conversation history."""

    def __init__(self):
        super().__init__(container_name="Conversations")

    async def create_conversation(
        self, user_id: str, first_message: Message
    ) -> Conversation:
        """Create a new conversation.

        Args:
            user_id: User ID
            first_message: First message in the conversation

        Returns:
            Created conversation
        """
        conv_id = str(uuid.uuid4())
        conversation = Conversation(
            id=conv_id,
            user_id=user_id,
            title=self._generate_title(first_message.content),
            messages=[first_message],
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat(),
        )
        await self.create(conversation.dict())
        logger.info(f"Created conversation {conv_id} for user {user_id}")
        return conversation

    async def get_conversation(self, conversation_id: str) -> Conversation | None:
        """Get conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation or None if not found
        """
        try:
            # Cosmos DB: id is partition key, so pass it as both id and partition_key
            item = await self.get_by_id(conversation_id, conversation_id)
            if item:
                return Conversation(**item)
            return None
        except Exception as e:
            logger.error(f"Error getting conversation {conversation_id}: {e}")
            return None

    async def add_message(
        self, conversation_id: str, message: Message
    ) -> Conversation:
        """Add message to conversation.

        Args:
            conversation_id: Conversation ID
            message: Message to add

        Returns:
            Updated conversation

        Raises:
            ValueError: If conversation not found
        """
        conv = await self.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        conv.messages.append(message)
        conv.updated_at = datetime.utcnow().isoformat()

        # Use upsert to update
        await self.upsert(conv.dict())
        logger.info(f"Added message to conversation {conversation_id}")
        return conv

    async def list_user_conversations(
        self, user_id: str, limit: int = 50
    ) -> list[Conversation]:
        """List conversations for a user.

        Args:
            user_id: User ID
            limit: Maximum number of conversations to return

        Returns:
            List of conversations
        """
        query = f"""
            SELECT * FROM c
            WHERE c.user_id = '{user_id}' AND c.is_active = true
            ORDER BY c.updated_at DESC
            OFFSET 0 LIMIT {limit}
        """
        items = await self.query(query)
        return [Conversation(**item) for item in items]

    async def delete_conversation(self, conversation_id: str) -> None:
        """Delete a conversation (soft delete).

        Args:
            conversation_id: Conversation ID to delete
        """
        conv = await self.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation {conversation_id} not found")

        conv_dict = conv.dict()
        conv_dict["is_active"] = False
        await self.upsert(conv_dict)
        logger.info(f"Deleted conversation {conversation_id}")

    def _generate_title(self, first_query: str) -> str:
        """Generate conversation title from first query.

        Args:
            first_query: First user query

        Returns:
            Generated title
        """
        # Simple version: first 30 characters
        # Phase 10: Use Gemini API for auto-generation
        return first_query[:30] + "..." if len(first_query) > 30 else first_query
