from datetime import datetime, timezone

from .repository_service import RepositoryService

class TodoService(RepositoryService):

    async def create(self, data):
        data["created_at"] = datetime.now(tz=timezone.utc)
        return await self.repository.create(data)

    async def update(self, object_id, data):
        data["updated_at"] = datetime.now(tz=timezone.utc)
        return await self.repository.update(object_id, data)
