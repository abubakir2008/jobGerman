from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import CandidateProfile
from app.schemas.profile import ProfileCreate, ProfileUpdate


class ProfileRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> CandidateProfile | None:
        result = await self.db.execute(
            select(CandidateProfile).where(CandidateProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: int, data: ProfileCreate) -> CandidateProfile:
        profile = CandidateProfile(user_id=user_id, **data.model_dump())
        self.db.add(profile)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    async def update(self, profile: CandidateProfile, data: ProfileUpdate) -> CandidateProfile:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile