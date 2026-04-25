import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class JobType(str, enum.Enum):
    seasonal = "seasonal"
    full_time = "full_time"


class JobStatus(str, enum.Enum):
    active = "active"
    closed = "closed"
    draft = "draft"


class JobCategory(Base, TimestampMixin):
    __tablename__ = "job_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)

    # Relationships
    jobs: Mapped[list["Job"]] = relationship(back_populates="category")

    def __repr__(self) -> str:
        return f"<JobCategory {self.name}>"


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_categories.id", ondelete="SET NULL")
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    requirements: Mapped[str | None] = mapped_column(Text)
    job_type: Mapped[JobType] = mapped_column(Enum(JobType), nullable=False, index=True)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.active)
    location: Mapped[str | None] = mapped_column(String(255))
    salary_min: Mapped[float | None] = mapped_column(Numeric(10, 2))
    salary_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    salary_currency: Mapped[str] = mapped_column(String(10), default="EUR")
    slots: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    category: Mapped["JobCategory"] = relationship(back_populates="jobs")
    applications: Mapped[list["Application"]] = relationship(back_populates="job")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Job {self.title} ({self.job_type})>" 