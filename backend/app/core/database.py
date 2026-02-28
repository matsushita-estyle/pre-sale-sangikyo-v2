"""Cosmos DB client management."""
from azure.cosmos import CosmosClient, PartitionKey
from app.core.config import settings


class CosmosDBClient:
    """Cosmos DB client wrapper."""

    def __init__(self):
        """Initialize Cosmos DB client."""
        self.client = CosmosClient(settings.COSMOS_ENDPOINT, settings.COSMOS_KEY)
        self.database = self.client.get_database_client(settings.COSMOS_DATABASE_NAME)

    def get_container(self, container_name: str):
        """Get container client."""
        return self.database.get_container_client(container_name)


# Global client instance
cosmos_client = CosmosDBClient()
