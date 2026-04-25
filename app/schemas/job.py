from pydantic import BaseModel, Field
from app.models.job import JobType, JobStatus


# ── Category ──────────────────────────────────────────────

class JobCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    description: str | None = None


class JobCategoryCreate(JobCategoryBase):
    pass


class JobCategoryResponse(JobCategoryBase):
    id: int

    model_config = {"from_attributes": True}


# ── Job ───────────────────────────────────────────────────

class JobBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    requirements: str | None = None
    job_type: JobType
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_currency: str = "EUR"
    slots: int = 1


class JobCreate(JobBase):
    category_id: int | None = None
    status: JobStatus = JobStatus.active


class JobUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    requirements: str | None = None
    location: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    slots: int | None = None
    status: JobStatus | None = None
    is_active: bool | None = None


class JobResponse(JobBase):
    id: int
    category_id: int | None
    status: JobStatus
    is_active: bool
    category: JobCategoryResponse | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list[JobResponse]
    total: int