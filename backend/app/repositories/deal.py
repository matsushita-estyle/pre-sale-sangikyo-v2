"""Deal repository for deal data access."""

import logging

from app.models.schemas import Deal
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class DealRepository(BaseRepository[Deal]):
    """Repository for Deal data access."""

    def __init__(self):
        """Initialize DealRepository."""
        super().__init__("Deals")

    async def get_all_deals(self) -> list[Deal]:
        """Get all deals.

        Returns:
            List of Deal objects
        """
        items = await self.get_all()
        return [Deal(**item) for item in items]

    async def get_deal_by_id(self, deal_id: str) -> Deal | None:
        """Get deal by ID.

        Args:
            deal_id: Deal ID

        Returns:
            Deal object or None if not found
        """
        item = await self.get_by_id(item_id=deal_id, partition_key=deal_id)
        return Deal(**item) if item else None

    async def get_deals_by_user(self, sales_user_id: str) -> list[Deal]:
        """Get deals by sales user.

        Args:
            sales_user_id: Sales user ID

        Returns:
            List of Deal objects
        """
        query = "SELECT * FROM c WHERE c.sales_user_id = @sales_user_id"
        parameters = [{"name": "@sales_user_id", "value": sales_user_id}]
        items = await self.query(query=query, parameters=parameters)
        return [Deal(**item) for item in items]

    async def get_deals_by_customer(self, customer_id: str) -> list[Deal]:
        """Get deals by customer.

        Args:
            customer_id: Customer ID

        Returns:
            List of Deal objects
        """
        query = "SELECT * FROM c WHERE c.customer_id = @customer_id"
        parameters = [{"name": "@customer_id", "value": customer_id}]
        items = await self.query(query=query, parameters=parameters)
        return [Deal(**item) for item in items]

    async def get_deals_by_stage(self, deal_stage: str) -> list[Deal]:
        """Get deals by stage.

        Args:
            deal_stage: Deal stage (見込み、提案、商談、受注、失注)

        Returns:
            List of Deal objects
        """
        query = "SELECT * FROM c WHERE c.deal_stage = @deal_stage"
        parameters = [{"name": "@deal_stage", "value": deal_stage}]
        items = await self.query(query=query, parameters=parameters)
        return [Deal(**item) for item in items]

    async def get_deals_by_service_type(self, service_type: str) -> list[Deal]:
        """Get deals by service type.

        Args:
            service_type: Service type

        Returns:
            List of Deal objects
        """
        query = "SELECT * FROM c WHERE c.service_type = @service_type"
        parameters = [{"name": "@service_type", "value": service_type}]
        items = await self.query(query=query, parameters=parameters)
        return [Deal(**item) for item in items]

    async def create_deal(self, deal: Deal) -> Deal:
        """Create a new deal.

        Args:
            deal: Deal object to create

        Returns:
            Created Deal object
        """
        deal_dict = deal.model_dump()
        deal_dict["id"] = deal.deal_id  # Cosmos DB requires 'id' field
        created = await self.create(deal_dict)
        return Deal(**created)

    async def update_deal(self, deal: Deal) -> Deal:
        """Update a deal.

        Args:
            deal: Deal object to update

        Returns:
            Updated Deal object
        """
        deal_dict = deal.model_dump()
        deal_dict["id"] = deal.deal_id
        updated = await self.upsert(deal_dict)
        return Deal(**updated)

    async def delete_deal(self, deal_id: str) -> None:
        """Delete a deal.

        Args:
            deal_id: Deal ID to delete
        """
        await self.delete(item_id=deal_id, partition_key=deal_id)
