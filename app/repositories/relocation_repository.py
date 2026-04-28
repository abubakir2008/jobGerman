from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.relocation import RelocationCase, RelocationStage
from app.models.application import Application, ApplicationStatus
from app.schemas.relocation import RelocationCaseUpdate


class RelocationCaseRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        manager_id: int | None = None,
        stage: RelocationStage | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[RelocationCase], int]:
        query = select(RelocationCase)

        if manager_id:
            query = query.where(RelocationCase.manager_id == manager_id)
        if stage:
            query = query.where(RelocationCase.stage == stage)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def get_by_id(self, case_id: int) -> RelocationCase | None:
        result = await self.db.execute(
            select(RelocationCase).where(RelocationCase.id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_by_application_id(self, application_id: int) -> RelocationCase | None:
        result = await self.db.execute(
            select(RelocationCase).where(RelocationCase.application_id == application_id)
        )
        return result.scalar_one_or_none()

    async def update(self, case: RelocationCase, data: RelocationCaseUpdate) -> RelocationCase:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(case, field, value)
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def get_application_status(self, case_id: int) -> ApplicationStatus | None:
        """Статус заявки для данного кейса."""
        result = await self.db.execute(
            select(Application.status)
            .join(RelocationCase, Application.id == RelocationCase.application_id)
            .where(RelocationCase.id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_candidate_user_id(self, case_id: int) -> int | None:
        """user_id кандидата для данного кейса."""
        result = await self.db.execute(
            select(Application.candidate_id)
            .join(RelocationCase, Application.id == RelocationCase.application_id)
            .where(RelocationCase.id == case_id)
        )
        return result.scalar_one_or_none() 