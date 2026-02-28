"""FastAPI dependencies for dependency injection."""
from app.repositories.user import UserRepository
from app.repositories.customer import CustomerRepository


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
