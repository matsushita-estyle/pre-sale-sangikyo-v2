"""Customer repository for customer data access."""

import logging

from app.models.schemas import Customer
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class CustomerRepository(BaseRepository[Customer]):
    """Repository for Customer data access."""

    def __init__(self):
        """Initialize CustomerRepository."""
        super().__init__("Customers")

    async def get_all_customers(self) -> list[Customer]:
        """Get all customers.

        Returns:
            List of Customer objects
        """
        items = await self.get_all()
        return [Customer(**item) for item in items]

    async def get_customer_by_id(self, customer_id: str) -> Customer | None:
        """Get customer by ID.

        Args:
            customer_id: Customer ID

        Returns:
            Customer object or None if not found
        """
        item = await self.get_by_id(item_id=customer_id, partition_key=customer_id)
        return Customer(**item) if item else None

    async def get_customers_by_industry(self, industry: str) -> list[Customer]:
        """Get customers by industry.

        Args:
            industry: Industry name

        Returns:
            List of Customer objects
        """
        query = "SELECT * FROM c WHERE c.industry = @industry"
        parameters = [{"name": "@industry", "value": industry}]
        items = await self.query(query=query, parameters=parameters)
        return [Customer(**item) for item in items]

    async def search_customers(self, keyword: str) -> list[Customer]:
        """Search customers by name.

        Args:
            keyword: Search keyword

        Returns:
            List of Customer objects matching the keyword
        """
        query = "SELECT * FROM c WHERE CONTAINS(c.name, @keyword)"
        parameters = [{"name": "@keyword", "value": keyword}]
        items = await self.query(query=query, parameters=parameters)
        return [Customer(**item) for item in items]

    async def create_customer(self, customer: Customer) -> Customer:
        """Create a new customer.

        Args:
            customer: Customer object to create

        Returns:
            Created Customer object
        """
        customer_dict = customer.model_dump()
        customer_dict["id"] = customer.customer_id  # Cosmos DB requires 'id' field
        created = await self.create(customer_dict)
        return Customer(**created)

    async def update_customer(self, customer: Customer) -> Customer:
        """Update a customer.

        Args:
            customer: Customer object to update

        Returns:
            Updated Customer object
        """
        customer_dict = customer.model_dump()
        customer_dict["id"] = customer.customer_id
        updated = await self.upsert(customer_dict)
        return Customer(**updated)

    async def delete_customer(self, customer_id: str) -> None:
        """Delete a customer.

        Args:
            customer_id: Customer ID to delete
        """
        await self.delete(item_id=customer_id, partition_key=customer_id)
