from fastapi import HTTPException, status

from app.models.job import JobType
from app.repositories.job_repositore import JobRepository, JobCategoryRepository
from app.schemas.job import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobCategoryCreate, JobCategoryResponse,
)


class JobCategoryService:

    def __init__(self, repo: JobCategoryRepository):
        self.repo = repo

    async def get_all(self) -> list[JobCategoryResponse]:
        categories = await self.repo.get_all()
        return [JobCategoryResponse.model_validate(c) for c in categories]

    async def create(self, data: JobCategoryCreate) -> JobCategoryResponse:
        category = await self.repo.create(data)
        return JobCategoryResponse.model_validate(category)


class JobService:

    def __init__(self, repo: JobRepository):
        self.repo = repo

    async def get_all(
        self,
        job_type: JobType | None = None,
        category_id: int | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> JobListResponse:
        jobs, total = await self.repo.get_all(
            job_type=job_type,
            category_id=category_id,
            offset=offset,
            limit=limit,
        )
        return JobListResponse(
            items=[JobResponse.model_validate(j) for j in jobs],
            total=total,
        )

    async def get_by_id(self, job_id: int) -> JobResponse:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )
        return JobResponse.model_validate(job)

    async def create(self, data: JobCreate) -> JobResponse:
        job = await self.repo.create(data)
        return JobResponse.model_validate(job)

    async def update(self, job_id: int, data: JobUpdate) -> JobResponse:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )
        updated = await self.repo.update(job, data)
        return JobResponse.model_validate(updated)

    async def delete(self, job_id: int) -> None:
        job = await self.repo.get_by_id(job_id)
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found",
            )
        await self.repo.delete(job)