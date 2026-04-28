from sqlalchemy import Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(
        ForeignKey("relocation_cases.id", ondelete="CASCADE"), nullable=False, index=True
    )
    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)

    case: Mapped["RelocationCase"] = relationship()  # noqa: F821
    sender: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<ChatMessage case={self.case_id} sender={self.sender_id}>"
