from app.models.notification import NotificationType
from app.repositories.notification_repository import NotificationRepository


class NotificationService:

    def __init__(self, repo: NotificationRepository):
        self.repo = repo

    async def notify(self, user_id: int, type: NotificationType, message: str):
        return await self.repo.create(user_id=user_id, type=type, message=message)

    async def get_my(self, user_id: int, offset: int = 0, limit: int = 30):
        items, total = await self.repo.get_by_user(user_id, offset, limit)
        return {"items": items, "total": total}

    async def mark_read(self, notif_id: int, user_id: int):
        notif = await self.repo.get_by_id(notif_id)
        if notif and notif.user_id == user_id:
            await self.repo.mark_read(notif_id)

    async def mark_all_read(self, user_id: int):
        await self.repo.mark_all_read(user_id)
