"""API routes."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.models.schemas import User, Customer
from app.repositories.user import UserRepository
from app.repositories.customer import CustomerRepository
from app.core.dependencies import get_user_repository, get_customer_repository
from app.core.exceptions import NotFoundException, DatabaseException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["data"])


# ============================================================
# User Endpoints
# ============================================================


@router.get("/users", response_model=List[User])
async def get_users(
    department: Optional[str] = Query(None, description="Filter by department"),
    role: Optional[str] = Query(None, description="Filter by role"),
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


@router.get("/customers", response_model=List[Customer])
async def get_customers(
    industry: Optional[str] = Query(None, description="Filter by industry"),
    search: Optional[str] = Query(None, description="Search by name"),
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
