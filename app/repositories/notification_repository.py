from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification, NotificationType


class NotificationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, type: NotificationType, message: str) -> Notification:
        notif = Notification(user_id=user_id, type=type, message=message)
        self.db.add(notif)
        await self.db.commit()
        await self.db.refresh(notif)
        return notif

    async def get_by_user(
        self, user_id: int, offset: int = 0, limit: int = 30
    ) -> tuple[list[Notification], int]:
        query = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
        )
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def get_by_id(self, notif_id: int) -> Notification | None:
        result = await self.db.execute(
            select(Notification).where(Notification.id == notif_id)
        )
        return result.scalar_one_or_none()

    async def mark_read(self, notif_id: int) -> None:
        await self.db.execute(
            update(Notification).where(Notification.id == notif_id).values(is_read=True)
        )
        await self.db.commit()

    async def mark_all_read(self, user_id: int) -> None:
        await self.db.execute(
            update(Notification)
            .where(Notification.user_id == user_id)
            .values(is_read=True)
        )
        await self.db.commit()
