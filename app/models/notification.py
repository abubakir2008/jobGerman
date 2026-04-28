import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class NotificationType(str, enum.Enum):
    stage_change = "stage_change"
    document_required = "document_required"
    manager_note = "manager_note"
    new_message = "new_message"


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Notification user={self.user_id} type={self.type}>"
