from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.repositories.profeli_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse
from app.service.profile_service import ProfileService

router = APIRouter()


def get_profile_service(db: AsyncSession = Depends(get_db)) -> ProfileService:
    return ProfileService(ProfileRepository(db))


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(
    user_id: int,
    service: ProfileService = Depends(get_profile_service),
):
    return await service.get_profile(user_id)


@router.post("/{user_id}", response_model=ProfileResponse, status_code=201)
async def create_profile(
    user_id: int,
    data: ProfileCreate,
    service: ProfileService = Depends(get_profile_service),
):
    return await service.create_profile(user_id, data)


@router.put("/{user_id}", response_model=ProfileResponse)
async def update_profile(
    user_id: int,
    data: ProfileUpdate,
    service: ProfileService = Depends(get_profile_service),
):
    return await service.update_profile(user_id, data) 