"""Repository layer for data access."""

from app.repositories.customer import CustomerRepository
from app.repositories.deal import DealRepository
from app.repositories.user import UserRepository

__all__ = ["UserRepository", "CustomerRepository", "DealRepository"]
