from pydantic import BaseModel, HttpUrl, Field
from app.models.media import MediaType, MediaCategory


class UsefulLink(BaseModel):
    label: str = Field(..., max_length=255, description="Название ссылки")
    url: str = Field(..., description="URL адрес")


class MediaResponse(BaseModel):
    id: int
    title: str
    description: str | None
    instruction: str | None
    useful_links: list[UsefulLink] | None
    media_type: MediaType
    category: MediaCategory
    file_url: str
    file_name: str
    file_size: int | None
    mime_type: str | None
    thumbnail_url: str | None
    is_published: bool

    model_config = {"from_attributes": True}


class MediaListResponse(BaseModel):
    items: list[MediaResponse]
    total: int


class MediaUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    instruction: str | None = None
    useful_links: list[UsefulLink] | None = None
    is_published: bool | None = None