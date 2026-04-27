from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.application import Application, ApplicationStatus
from app.models.relocation import RelocationCase
from app.schemas.appliction import ApplicationCreate, ApplicationUpdate


class ApplicationRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        candidate_id: int | None = None,
        job_id: int | None = None,
        status: ApplicationStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Application], int]:
        query = (
            select(Application)
            .options(selectinload(Application.relocation_case))
        )
        if candidate_id:
            query = query.where(Application.candidate_id == candidate_id)
        if job_id:
            query = query.where(Application.job_id == job_id)
        if status:
            query = query.where(Application.status == status)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def get_by_id(self, application_id: int) -> Application | None:
        result = await self.db.execute(
            select(Application)
            .options(selectinload(Application.relocation_case))
            .where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def get_by_candidate_and_job(
        self, candidate_id: int, job_id: int
    ) -> Application | None:
        result = await self.db.execute(
            select(Application).where(
                Application.candidate_id == candidate_id,
                Application.job_id == job_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, candidate_id: int, data: ApplicationCreate) -> Application:
        application = Application(candidate_id=candidate_id, **data.model_dump())
        self.db.add(application)
        await self.db.flush()

        relocation_case = RelocationCase(application_id=application.id)
        self.db.add(relocation_case)
        await self.db.commit()

        # Перезагружаем с relocation_case
        result = await self.db.execute(
            select(Application)
            .options(selectinload(Application.relocation_case))
            .where(Application.id == application.id)
        )
        return result.scalar_one()

    async def update(self, application: Application, data: ApplicationUpdate) -> Application:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(application, field, value)
        await self.db.commit()

        # Перезагружаем с relocation_case
        result = await self.db.execute(
            select(Application)
            .options(selectinload(Application.relocation_case))
            .where(Application.id == application.id)
        )
        return result.scalar_one()