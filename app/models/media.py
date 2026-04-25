import enum
from typing import Any

from sqlalchemy import Enum, JSON, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class MediaType(str, enum.Enum):
    video = "video"
    image = "image"
    document = "document"


class MediaCategory(str, enum.Enum):
    visa = "visa"
    interview = "interview"
    relocation = "relocation"
    work_in_germany = "work_in_germany"


class Media(Base, TimestampMixin):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    # Текстовое описание / инструкция к уроку
    description: Mapped[str | None] = mapped_column(Text)

    # Подробная инструкция (markdown или plain text)
    instruction: Mapped[str | None] = mapped_column(Text)

    # Полезные ссылки: [{"label": "Официальный сайт", "url": "https://..."}]
    useful_links: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, default=list)

    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType), nullable=False)
    category: Mapped[MediaCategory] = mapped_column(Enum(MediaCategory), nullable=False, index=True)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int | None] = mapped_column()
    mime_type: Mapped[str | None] = mapped_column(String(100))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<Media {self.title} ({self.media_type})>"