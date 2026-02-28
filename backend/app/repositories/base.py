"""Base repository for common CRUD operations."""
import logging
from typing import List, Optional, TypeVar, Generic
from azure.cosmos import ContainerProxy
from app.core.database import cosmos_client

logger = logging.getLogger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, container_name: str):
        """Initialize repository with container name.

        Args:
            container_name: Name of the Cosmos DB container
        """
        self.container_name = container_name
        self.container: ContainerProxy = cosmos_client.get_container(container_name)
        logger.debug(f"Repository initialized for container: {container_name}")

    async def get_all(self) -> List[dict]:
        """Get all items from the container.

        Returns:
            List of all items
        """
        try:
            query = "SELECT * FROM c"
            items = list(
                self.container.query_items(
                    query=query, enable_cross_partition_query=True
                )
            )
            logger.info(f"Retrieved {len(items)} items from {self.container_name}")
            return items
        except Exception as e:
            logger.error(f"Error getting all items from {self.container_name}: {e}")
            raise

    async def get_by_id(self, item_id: str, partition_key: str) -> Optional[dict]:
        """Get item by ID.

        Args:
            item_id: Item ID
            partition_key: Partition key value

        Returns:
            Item dict or None if not found
        """
        try:
            item = self.container.read_item(item=item_id, partition_key=partition_key)
            logger.debug(f"Retrieved item {item_id} from {self.container_name}")
            return item
        except Exception as e:
            logger.warning(f"Item {item_id} not found in {self.container_name}: {e}")
            return None

    async def query(self, query: str, parameters: Optional[List] = None) -> List[dict]:
        """Execute a custom query.

        Args:
            query: SQL query string
            parameters: Query parameters

        Returns:
            List of matching items
        """
        try:
            items = list(
                self.container.query_items(
                    query=query,
                    parameters=parameters or [],
                    enable_cross_partition_query=True,
                )
            )
            logger.debug(f"Query returned {len(items)} items from {self.container_name}")
            return items
        except Exception as e:
            logger.error(f"Error executing query on {self.container_name}: {e}")
            raise

    async def create(self, item: dict) -> dict:
        """Create a new item.

        Args:
            item: Item to create

        Returns:
            Created item
        """
        try:
            created_item = self.container.create_item(body=item)
            logger.info(f"Created item in {self.container_name}: {item.get('id')}")
            return created_item
        except Exception as e:
            logger.error(f"Error creating item in {self.container_name}: {e}")
            raise

    async def upsert(self, item: dict) -> dict:
        """Create or update an item.

        Args:
            item: Item to upsert

        Returns:
            Upserted item
        """
        try:
            upserted_item = self.container.upsert_item(body=item)
            logger.info(f"Upserted item in {self.container_name}: {item.get('id')}")
            return upserted_item
        except Exception as e:
            logger.error(f"Error upserting item in {self.container_name}: {e}")
            raise

    async def delete(self, item_id: str, partition_key: str) -> None:
        """Delete an item.

        Args:
            item_id: Item ID
            partition_key: Partition key value
        """
        try:
            self.container.delete_item(item=item_id, partition_key=partition_key)
            logger.info(f"Deleted item {item_id} from {self.container_name}")
        except Exception as e:
            logger.error(f"Error deleting item {item_id} from {self.container_name}: {e}")
            raise
