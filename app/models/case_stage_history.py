from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.relocation import RelocationStage


class CaseStageHistory(Base):
    __tablename__ = "case_stage_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("relocation_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    stage: Mapped[RelocationStage] = mapped_column(Enum(RelocationStage), nullable=False)
    changed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    note: Mapped[str | None] = mapped_column(Text)

    case: Mapped["RelocationCase"] = relationship()  # noqa: F821
    changed_by: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<CaseStageHistory case={self.case_id} stage={self.stage}>"
