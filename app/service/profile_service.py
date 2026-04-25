from fastapi import HTTPException, status

from app.repositories.profeli_repository import ProfileRepository
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileResponse


class ProfileService:

    def __init__(self, repo: ProfileRepository):
        self.repo = repo

    async def get_profile(self, user_id: int) -> ProfileResponse:
        profile = await self.repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create your profile first.",
            )
        return ProfileResponse.model_validate(profile)

    async def create_profile(self, user_id: int, data: ProfileCreate) -> ProfileResponse:
        existing = await self.repo.get_by_user_id(user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Profile already exists. Use PUT to update it.",
            )
        profile = await self.repo.create(user_id, data)
        return ProfileResponse.model_validate(profile)

    async def update_profile(self, user_id: int, data: ProfileUpdate) -> ProfileResponse:
        profile = await self.repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Please create your profile first.",
            )
        updated = await self.repo.update(profile, data)
        return ProfileResponse.model_validate(updated) 