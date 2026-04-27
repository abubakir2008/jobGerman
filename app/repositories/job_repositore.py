from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.job import Job, JobCategory, JobType, JobStatus
from app.schemas.job import JobCreate, JobUpdate, JobCategoryCreate


class JobCategoryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> list[JobCategory]:
        result = await self.db.execute(select(JobCategory))
        return result.scalars().all()

    async def get_by_id(self, category_id: int) -> JobCategory | None:
        result = await self.db.execute(
            select(JobCategory).where(JobCategory.id == category_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: JobCategoryCreate) -> JobCategory:
        category = JobCategory(**data.model_dump())
        self.db.add(category)
        await self.db.commit()
        await self.db.refresh(category)
        return category


class JobRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        job_type: JobType | None = None,
        category_id: int | None = None,
        is_active: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Job], int]:
        query = (
            select(Job)
            .options(selectinload(Job.category))
            .where(Job.is_active == is_active)
        )

        if job_type:
            query = query.where(Job.job_type == job_type)
        if category_id:
            query = query.where(Job.category_id == category_id)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_by_id(self, job_id: int) -> Job | None:
        result = await self.db.execute(
            select(Job)
            .options(selectinload(Job.category))
            .where(Job.id == job_id)
        )
        return result.scalar_one_or_none()

    async def create(self, data: JobCreate) -> Job:
        job = Job(**data.model_dump())
        self.db.add(job)
        await self.db.commit()

        # Перезагружаем с category
        result = await self.db.execute(
            select(Job)
            .options(selectinload(Job.category))
            .where(Job.id == job.id)
        )
        return result.scalar_one()

    async def update(self, job: Job, data: JobUpdate) -> Job:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(job, field, value)
        await self.db.commit()

        # Перезагружаем с category
        result = await self.db.execute(
            select(Job)
            .options(selectinload(Job.category))
            .where(Job.id == job.id)
        )
        return result.scalar_one()

    async def delete(self, job: Job) -> None:
        await self.db.delete(job)
        await self.db.commit()