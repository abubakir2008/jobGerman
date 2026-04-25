import enum

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.relocation import RelocationCase


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    reviewing = "reviewing"
    accepted = "accepted"
    rejected = "rejected"
    withdrawn = "withdrawn"


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus), default=ApplicationStatus.pending, index=True
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)

    # Relationships
    candidate: Mapped["User"] = relationship(back_populates="applications")  # noqa: F821
    job: Mapped["Job"] = relationship(back_populates="applications")  # noqa: F821
    relocation_case: Mapped["RelocationCase"] = relationship(  # noqa: F821
        back_populates="application", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Application candidate={self.candidate_id} job={self.job_id}>"
