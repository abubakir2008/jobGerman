from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.user import User
from app.repositories.notification_repository import NotificationRepository
from app.service.notification_service import NotificationService

router = APIRouter()


def get_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(NotificationRepository(db))


@router.get("")
async def get_notifications(
    offset: int = Query(0, ge=0),
    limit: int = Query(30, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_service),
):
    return await service.get_my(current_user.id, offset, limit)


@router.post("/{notif_id}/read")
async def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_service),
):
    await service.mark_read(notif_id, current_user.id)
    return {"ok": True}


@router.post("/read-all")
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_service),
):
    await service.mark_all_read(current_user.id)
    return {"ok": True}
