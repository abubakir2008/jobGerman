import enum
from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class RelocationStage(str, enum.Enum):
    applied = "applied"
    interview = "interview"
    documents = "documents"
    visa = "visa"
    relocation = "relocation"
    completed = "completed"


class RelocationCase(Base, TimestampMixin):
    __tablename__ = "relocation_cases"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    manager_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    stage: Mapped[RelocationStage] = mapped_column(
        Enum(RelocationStage), default=RelocationStage.applied, index=True
    )
    notes: Mapped[str | None] = mapped_column(Text)
    stage_deadline: Mapped[date | None] = mapped_column(Date)

    # Relationships
    application: Mapped["Application"] = relationship(back_populates="relocation_case")  # noqa: F821
    manager: Mapped["User"] = relationship(back_populates="managed_cases")  # noqa: F821

    def __repr__(self) -> str:
        return f"<RelocationCase application={self.application_id} stage={self.stage}>" 