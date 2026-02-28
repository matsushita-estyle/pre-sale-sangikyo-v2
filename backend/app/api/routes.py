"""API routes."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.dependencies import get_customer_repository, get_deal_repository, get_user_repository
from app.core.exceptions import NotFoundException
from app.models.schemas import ChatRequest, ChatResponse, Customer, Deal, User
from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository
from app.repositories.user import UserRepository
from app.services.copilot_service import CopilotService, get_copilot_service
from app.schemas.agent import AgentQueryRequest, ProgressEvent, ProgressEventType
from app.agent.mock_orchestrator import MockAgentOrchestrator

logger = logging.getLogger(__name__)

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
# Agent (SSE Streaming) Endpoints
# ============================================================


@router.post("/agent/query-stream")
async def agent_query_stream(request: AgentQueryRequest):
    """
    エージェントクエリ（SSEストリーミング）

    進捗状況をリアルタイムで返す（モック版）

    Args:
        request: Agent query request with user_id and query

    Returns:
        Server-Sent Events stream
    """
    orchestrator = MockAgentOrchestrator()

    async def generate():
        try:
            async for event in orchestrator.execute_query_stream(
                request.user_id, request.query
            ):
                # ProgressEventをJSON化してSSEフォーマットで送信
                yield f"data: {event.model_dump_json()}\n\n"
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
