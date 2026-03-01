"""API routes."""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_customer_repository, get_deal_repository, get_user_repository
from app.core.exceptions import NotFoundException
from app.models.schemas import ChatRequest, ChatResponse, Customer, Deal, User
from app.models.conversation import Message, Conversation
from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository
from app.repositories.user import UserRepository
from app.repositories.conversation import ConversationRepository
from app.services.copilot_service import CopilotService, get_copilot_service
from app.schemas.agent import AgentQueryRequest, ProgressEvent, ProgressEventType, ConversationResponse
from app.agent.orchestrator import AgentOrchestrator
# from app.agent.mock_orchestrator import MockAgentOrchestrator  # モック版（テスト用に残す）

logger = logging.getLogger(__name__)


# ============================================================
# Dependency Injection
# ============================================================


def get_conversation_repository() -> ConversationRepository:
    """Get conversation repository instance."""
    return ConversationRepository()

router = APIRouter(prefix="/api/v1", tags=["data"])


# ============================================================
# User Endpoints
# ============================================================


@router.get("/users", response_model=list[User])
async def get_users(
    department: str | None = Query(None, description="Filter by department"),
    role: str | None = Query(None, description="Filter by role"),
    repo: UserRepository = Depends(get_user_repository),
):
    """Get all users or filter by department/role.

    Args:
        department: Optional department filter
        role: Optional role filter
        repo: UserRepository dependency

    Returns:
        List of users
    """
    try:
        if department:
            logger.info(f"Fetching users by department: {department}")
            return await repo.get_users_by_department(department)
        elif role:
            logger.info(f"Fetching users by role: {role}")
            return await repo.get_users_by_role(role)
        else:
            logger.info("Fetching all users")
            return await repo.get_all_users()
    except Exception as e:
        logger.error(f"Error fetching users: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    repo: UserRepository = Depends(get_user_repository),
):
    """Get user by ID.

    Args:
        user_id: User ID
        repo: UserRepository dependency

    Returns:
        User object
    """
    try:
        logger.info(f"Fetching user: {user_id}")
        user = await repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundException(f"User {user_id} not found")
        return user
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    except Exception as e:
        logger.error(f"Error fetching user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching user: {str(e)}")


# ============================================================
# Customer Endpoints
# ============================================================


@router.get("/customers", response_model=list[Customer])
async def get_customers(
    industry: str | None = Query(None, description="Filter by industry"),
    search: str | None = Query(None, description="Search by name"),
    repo: CustomerRepository = Depends(get_customer_repository),
):
    """Get all customers or filter by industry/search.

    Args:
        industry: Optional industry filter
        search: Optional search keyword
        repo: CustomerRepository dependency

    Returns:
        List of customers
    """
    try:
        if industry:
            logger.info(f"Fetching customers by industry: {industry}")
            return await repo.get_customers_by_industry(industry)
        elif search:
            logger.info(f"Searching customers: {search}")
            return await repo.search_customers(search)
        else:
            logger.info("Fetching all customers")
            return await repo.get_all_customers()
    except Exception as e:
        logger.error(f"Error fetching customers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching customers: {str(e)}")


@router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(
    customer_id: str,
    repo: CustomerRepository = Depends(get_customer_repository),
):
    """Get customer by ID.

    Args:
        customer_id: Customer ID
        repo: CustomerRepository dependency

    Returns:
        Customer object
    """
    try:
        logger.info(f"Fetching customer: {customer_id}")
        customer = await repo.get_customer_by_id(customer_id)
        if not customer:
            raise NotFoundException(f"Customer {customer_id} not found")
        return customer
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
    except Exception as e:
        logger.error(f"Error fetching customer {customer_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching customer: {str(e)}")


# ============================================================
# Deal Endpoints
# ============================================================


@router.get("/deals", response_model=list[Deal])
async def get_deals(
    sales_user_id: str | None = Query(None, description="Filter by sales user ID"),
    customer_id: str | None = Query(None, description="Filter by customer ID"),
    deal_stage: str | None = Query(None, description="Filter by deal stage"),
    service_type: str | None = Query(None, description="Filter by service type"),
    repo: DealRepository = Depends(get_deal_repository),
):
    """Get all deals or filter by various criteria.

    Args:
        sales_user_id: Optional sales user ID filter
        customer_id: Optional customer ID filter
        deal_stage: Optional deal stage filter (見込み、提案、商談、受注、失注)
        service_type: Optional service type filter (通信インフラ構築、技術人材派遣、危機管理対策)
        repo: DealRepository dependency

    Returns:
        List of deals
    """
    try:
        if sales_user_id:
            logger.info(f"Fetching deals by sales user: {sales_user_id}")
            return await repo.get_deals_by_user(sales_user_id)
        elif customer_id:
            logger.info(f"Fetching deals by customer: {customer_id}")
            return await repo.get_deals_by_customer(customer_id)
        elif deal_stage:
            logger.info(f"Fetching deals by stage: {deal_stage}")
            return await repo.get_deals_by_stage(deal_stage)
        elif service_type:
            logger.info(f"Fetching deals by service type: {service_type}")
            return await repo.get_deals_by_service_type(service_type)
        else:
            logger.info("Fetching all deals")
            return await repo.get_all_deals()
    except Exception as e:
        logger.error(f"Error fetching deals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching deals: {str(e)}")


@router.get("/deals/{deal_id}", response_model=Deal)
async def get_deal(
    deal_id: str,
    repo: DealRepository = Depends(get_deal_repository),
):
    """Get deal by ID.

    Args:
        deal_id: Deal ID
        repo: DealRepository dependency

    Returns:
        Deal object
    """
    try:
        logger.info(f"Fetching deal: {deal_id}")
        deal = await repo.get_deal_by_id(deal_id)
        if not deal:
            raise NotFoundException(f"Deal {deal_id} not found")
        return deal
    except NotFoundException:
        raise HTTPException(status_code=404, detail=f"Deal {deal_id} not found")
    except Exception as e:
        logger.error(f"Error fetching deal {deal_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching deal: {str(e)}")


# ============================================================
# Copilot (AI Chat) Endpoints
# ============================================================


@router.post("/copilot/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    copilot_service: CopilotService = Depends(get_copilot_service),
):
    """
    AI chat endpoint.

    Args:
        request: Chat request with user_id and query
        copilot_service: CopilotService dependency

    Returns:
        AI-generated response
    """
    try:
        logger.info(f"Chat request from user {request.user_id}: {request.query[:50]}...")
        response_text = await copilot_service.chat(request.user_id, request.query)
        return ChatResponse(response=response_text)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


# ============================================================
# Conversation History Endpoints
# ============================================================


def convert_to_gemini_format(messages: list[Message]) -> list[dict]:
    """Convert Message objects to Gemini chat history format.

    Args:
        messages: List of Message objects

    Returns:
        List of dicts in Gemini format
    """
    gemini_history = []
    for msg in messages:
        gemini_history.append({
            "role": msg.role if msg.role == "user" else "model",
            "parts": [{"text": msg.content}],
        })
    return gemini_history


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    user_id: str,
    first_message_content: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
):
    """Create a new conversation.

    Args:
        user_id: User ID
        first_message_content: First message content
        repo: ConversationRepository dependency

    Returns:
        Created conversation
    """
    try:
        first_message = Message(
            message_id=str(uuid.uuid4()),
            role="user",
            content=first_message_content,
            timestamp=datetime.utcnow().isoformat(),
        )
        conversation = await repo.create_conversation(user_id, first_message)
        logger.info(f"Created conversation {conversation.id}")
        return ConversationResponse(**conversation.dict())
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating conversation: {str(e)}")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
):
    """Get conversation by ID.

    Args:
        conversation_id: Conversation ID
        repo: ConversationRepository dependency

    Returns:
        Conversation object
    """
    try:
        conversation = await repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
        return ConversationResponse(**conversation.dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting conversation: {str(e)}")


@router.get("/users/{user_id}/conversations", response_model=list[ConversationResponse])
async def list_user_conversations(
    user_id: str,
    limit: int = Query(50, description="Max number of conversations to return"),
    repo: ConversationRepository = Depends(get_conversation_repository),
):
    """List conversations for a user.

    Args:
        user_id: User ID
        limit: Max number of conversations
        repo: ConversationRepository dependency

    Returns:
        List of conversations
    """
    try:
        conversations = await repo.list_user_conversations(user_id, limit)
        return [ConversationResponse(**c.dict()) for c in conversations]
    except Exception as e:
        logger.error(f"Error listing conversations for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error listing conversations: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    repo: ConversationRepository = Depends(get_conversation_repository),
):
    """Delete a conversation (soft delete).

    Args:
        conversation_id: Conversation ID to delete
        repo: ConversationRepository dependency

    Returns:
        Success message
    """
    try:
        await repo.delete_conversation(conversation_id)
        return {"message": "Conversation deleted successfully"}
    except ValueError as e:
        logger.error(f"Conversation not found: {conversation_id}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting conversation {conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")


# ============================================================
# Agent (SSE Streaming) Endpoints
# ============================================================


@router.post("/agent/query-stream")
async def agent_query_stream(
    request: AgentQueryRequest,
    conv_repo: ConversationRepository = Depends(get_conversation_repository),
):
    """
    エージェントクエリ（SSEストリーミング）

    Gemini Function Calling Agentを使用して進捗状況をリアルタイムで返す

    Args:
        request: Agent query request with user_id, query, and optional conversation_id
        conv_repo: ConversationRepository dependency

    Returns:
        Server-Sent Events stream
    """
    orchestrator = AgentOrchestrator()

    # 会話履歴の処理
    conversation_id = request.conversation_id
    conversation_history = None

    if conversation_id:
        # 既存の会話を取得
        conversation = await conv_repo.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

        # Gemini形式に変換
        conversation_history = convert_to_gemini_format(conversation.messages)
        logger.info(f"Loaded {len(conversation.messages)} messages from conversation {conversation_id}")
    else:
        # 新規会話を作成
        first_message = Message(
            message_id=str(uuid.uuid4()),
            role="user",
            content=request.query,
            timestamp=datetime.utcnow().isoformat(),
        )
        conversation = await conv_repo.create_conversation(request.user_id, first_message)
        conversation_id = conversation.id
        logger.info(f"Created new conversation {conversation_id}")

    async def generate():
        final_response_text = None
        first_event = True
        try:
            # ユーザーメッセージを保存（既存会話の場合のみ）
            if request.conversation_id:
                user_message = Message(
                    message_id=str(uuid.uuid4()),
                    role="user",
                    content=request.query,
                    timestamp=datetime.utcnow().isoformat(),
                )
                await conv_repo.add_message(conversation_id, user_message)
                logger.debug(f"Saved user message to conversation {conversation_id}")

            # エージェント実行
            async for event in orchestrator.execute_query_stream(
                request.user_id, request.query, conversation_history
            ):
                # 最初のイベントにconversation_idを追加
                if first_event:
                    event.conversation_id = conversation_id
                    first_event = False

                # 最終レスポンスを保存
                if event.type == ProgressEventType.FINAL_RESPONSE:
                    final_response_text = event.content

                # ProgressEventをJSON化してSSEフォーマットで送信
                yield f"data: {event.model_dump_json()}\n\n"

            # アシスタントメッセージを保存
            if final_response_text:
                assistant_message = Message(
                    message_id=str(uuid.uuid4()),
                    role="assistant",
                    content=final_response_text,
                    timestamp=datetime.utcnow().isoformat(),
                )
                await conv_repo.add_message(conversation_id, assistant_message)
                logger.info(f"Saved assistant message to conversation {conversation_id}")

        except Exception as e:
            # エラー時もSSEで送信
            logger.error(f"Error in agent query stream: {e}", exc_info=True)
            error_event = ProgressEvent(
                type=ProgressEventType.ERROR, message=str(e)
            )
            yield f"data: {error_event.model_dump_json()}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Nginx buffering無効化
        },
    )
