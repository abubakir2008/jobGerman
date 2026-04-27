from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import require_admin
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRoleUpdate, UserResponse, UserListResponse

router = APIRouter()


def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


@router.get("", response_model=UserListResponse)
async def get_all_users(
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user=Depends(require_admin),
    repo: UserRepository = Depends(get_user_repo),
):
    """Список всех пользователей — только для админов."""
    users, total = await repo.get_all(offset=offset, limit=limit)
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user=Depends(require_admin),
    repo: UserRepository = Depends(get_user_repo),
):
    """Получить пользователя по id — только для админов."""
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )
    return UserResponse.model_validate(user)


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    data: UserRoleUpdate,
    current_user=Depends(require_admin),
    repo: UserRepository = Depends(get_user_repo),
):
    """Сменить роль пользователя — только для админов."""
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found.",
        )
    updated = await repo.update_role(user, data)
    return UserResponse.model_validate(updated)