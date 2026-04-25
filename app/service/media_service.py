import uuid

from fastapi import HTTPException, UploadFile, status

from app.models.media import MediaType, MediaCategory
from app.repositories.media_repository import MediaRepository
from app.schemas.media import MediaResponse, MediaListResponse, MediaUpdate, UsefulLink
from app.storage.minio import upload_file, delete_file

ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/webm",
    "image/jpeg",
    "image/png",
    "image/webp",
    "application/pdf",
}

MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB


class MediaService:

    def __init__(self, repo: MediaRepository):
        self.repo = repo

    async def get_all(
        self,
        media_type: MediaType | None = None,
        category: MediaCategory | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> MediaListResponse:
        items, total = await self.repo.get_all(
            media_type=media_type,
            category=category,
            offset=offset,
            limit=limit,
        )
        return MediaListResponse(
            items=[MediaResponse.model_validate(m) for m in items],
            total=total,
        )

    async def get_by_id(self, media_id: int) -> MediaResponse:
        media = await self.repo.get_by_id(media_id)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media {media_id} not found.",
            )
        return MediaResponse.model_validate(media)

    async def upload(
        self,
        title: str,
        description: str | None,
        instruction: str | None,
        useful_links: list[UsefulLink] | None,
        media_type: MediaType,
        category: MediaCategory,
        file: UploadFile,
    ) -> MediaResponse:
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File type not allowed. Allowed: MP4, WEBM, JPEG, PNG, WEBP, PDF.",
            )

        file_data = await file.read()
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 200 MB.",
            )

        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
        object_name = f"media/{category}/{media_type}/{uuid.uuid4()}.{ext}"
        file_url = upload_file(file_data, object_name, file.content_type)

        media = await self.repo.create(
            title=title,
            description=description,
            instruction=instruction,
            useful_links=useful_links,
            media_type=media_type,
            category=category,
            file_url=file_url,
            file_name=file.filename,
            file_size=len(file_data),
            mime_type=file.content_type,
            thumbnail_url=None,
        )
        return MediaResponse.model_validate(media)

    async def update(self, media_id: int, data: MediaUpdate) -> MediaResponse:
        media = await self.repo.get_by_id(media_id)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media {media_id} not found.",
            )
        updated = await self.repo.update(media, data)
        return MediaResponse.model_validate(updated)

    async def delete(self, media_id: int) -> None:
        media = await self.repo.get_by_id(media_id)
        if not media:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Media {media_id} not found.",
            )
        try:
            object_name = media.file_url.split("/", 3)[-1]
            delete_file(object_name)
        except Exception:
            pass
        await self.repo.delete(media) 