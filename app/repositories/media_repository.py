from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import Media, MediaType, MediaCategory
from app.schemas.media import MediaUpdate, UsefulLink


class MediaRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        media_type: MediaType | None = None,
        category: MediaCategory | None = None,
        is_published: bool = True,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[Media], int]:
        query = select(Media).where(Media.is_published == is_published)

        if media_type:
            query = query.where(Media.media_type == media_type)
        if category:
            query = query.where(Media.category == category)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def get_by_id(self, media_id: int) -> Media | None:
        result = await self.db.execute(
            select(Media).where(Media.id == media_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        title: str,
        description: str | None,
        instruction: str | None,
        useful_links: list[UsefulLink] | None,
        media_type: MediaType,
        category: MediaCategory,
        file_url: str,
        file_name: str,
        file_size: int | None,
        mime_type: str | None,
        thumbnail_url: str | None,
    ) -> Media:
        media = Media(
            title=title,
            description=description,
            instruction=instruction,
            useful_links=[l.model_dump() for l in useful_links] if useful_links else [],
            media_type=media_type,
            category=category,
            file_url=file_url,
            file_name=file_name,
            file_size=file_size,
            mime_type=mime_type,
            thumbnail_url=thumbnail_url,
        )
        self.db.add(media)
        await self.db.commit()
        await self.db.refresh(media)
        return media

    async def update(self, media: Media, data: MediaUpdate) -> Media:
        update_data = data.model_dump(exclude_unset=True)
        if "useful_links" in update_data and update_data["useful_links"] is not None:
            update_data["useful_links"] = [
                l.model_dump() for l in data.useful_links
            ]
        for field, value in update_data.items():
            setattr(media, field, value)
        await self.db.commit()
        await self.db.refresh(media)
        return media

    async def delete(self, media: Media) -> None:
        await self.db.delete(media)
        await self.db.commit() 