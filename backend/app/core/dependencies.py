"""FastAPI dependencies for dependency injection."""

from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository
from app.repositories.user import UserRepository


def get_user_repository() -> UserRepository:
    """Provide UserRepository instance.

    Returns:
        UserRepository instance
    """
    return UserRepository()


def get_customer_repository() -> CustomerRepository:
    """Provide CustomerRepository instance.

    Returns:
        CustomerRepository instance
    """
    return CustomerRepository()


def get_deal_repository() -> DealRepository:
    """Provide DealRepository instance.

    Returns:
        DealRepository instance
    """
    return DealRepository()
