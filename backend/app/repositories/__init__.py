"""Repository layer for data access."""
from app.repositories.user import UserRepository
from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository

__all__ = ["UserRepository", "CustomerRepository", "DealRepository"]
