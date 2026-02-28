"""User repository for user data access."""
import logging
from typing import List, Optional
from app.repositories.base import BaseRepository
from app.models.schemas import User

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User data access."""

    def __init__(self):
        """Initialize UserRepository."""
        super().__init__("Users")

    async def get_all_users(self) -> List[User]:
        """Get all users.

        Returns:
            List of User objects
        """
        items = await self.get_all()
        return [User(**item) for item in items]

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        item = await self.get_by_id(item_id=user_id, partition_key=user_id)
        return User(**item) if item else None

    async def get_users_by_department(self, department: str) -> List[User]:
        """Get users by department.

        Args:
            department: Department name

        Returns:
            List of User objects
        """
        query = "SELECT * FROM c WHERE c.department = @department"
        parameters = [{"name": "@department", "value": department}]
        items = await self.query(query=query, parameters=parameters)
        return [User(**item) for item in items]

    async def get_users_by_role(self, role: str) -> List[User]:
        """Get users by role.

        Args:
            role: Role name

        Returns:
            List of User objects
        """
        query = "SELECT * FROM c WHERE c.role = @role"
        parameters = [{"name": "@role", "value": role}]
        items = await self.query(query=query, parameters=parameters)
        return [User(**item) for item in items]

    async def create_user(self, user: User) -> User:
        """Create a new user.

        Args:
            user: User object to create

        Returns:
            Created User object
        """
        user_dict = user.model_dump()
        user_dict["id"] = user.user_id  # Cosmos DB requires 'id' field
        created = await self.create(user_dict)
        return User(**created)

    async def update_user(self, user: User) -> User:
        """Update a user.

        Args:
            user: User object to update

        Returns:
            Updated User object
        """
        user_dict = user.model_dump()
        user_dict["id"] = user.user_id
        updated = await self.upsert(user_dict)
        return User(**updated)

    async def delete_user(self, user_id: str) -> None:
        """Delete a user.

        Args:
            user_id: User ID to delete
        """
        await self.delete(item_id=user_id, partition_key=user_id)
