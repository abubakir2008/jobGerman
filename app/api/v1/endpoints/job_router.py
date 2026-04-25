from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.job import JobType
from app.repositories.job_repositore import JobRepository, JobCategoryRepository
from app.schemas.job import (
    JobCreate, JobUpdate, JobResponse, JobListResponse,
    JobCategoryCreate, JobCategoryResponse,
)
from app.service.job_service import JobService, JobCategoryService

router = APIRouter()


# ── Dependencies ──────────────────────────────────────────

def get_job_service(db: AsyncSession = Depends(get_db)) -> JobService:
    return JobService(JobRepository(db))


def get_category_service(db: AsyncSession = Depends(get_db)) -> JobCategoryService:
    return JobCategoryService(JobCategoryRepository(db))


# ── Categories ────────────────────────────────────────────

@router.get("/categories", response_model=list[JobCategoryResponse])
async def get_categories(service: JobCategoryService = Depends(get_category_service)):
    return await service.get_all()


@router.post("/categories", response_model=JobCategoryResponse, status_code=201)
async def create_category(
    data: JobCategoryCreate,
    service: JobCategoryService = Depends(get_category_service),
):
    return await service.create(data)


# ── Jobs ──────────────────────────────────────────────────

@router.get("", response_model=JobListResponse)
async def get_jobs(
    job_type: JobType | None = Query(None, description="seasonal / full_time"),
    category_id: int | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: JobService = Depends(get_job_service),
):
    return await service.get_all(
        job_type=job_type,
        category_id=category_id,
        offset=offset,
        limit=limit,
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: int, service: JobService = Depends(get_job_service)):
    return await service.get_by_id(job_id)


@router.post("", response_model=JobResponse, status_code=201)
async def create_job(data: JobCreate, service: JobService = Depends(get_job_service)):
    return await service.create(data)


@router.patch("/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: int,
    data: JobUpdate,
    service: JobService = Depends(get_job_service),
):
    return await service.update(job_id, data)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: int, service: JobService = Depends(get_job_service)):
    await service.delete(job_id) 