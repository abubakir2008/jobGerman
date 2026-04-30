import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user, require_admin
from app.models.media import MediaType, MediaCategory
from app.models.user import User
from app.repositories.media_repository import MediaRepository
from app.schemas.media import MediaResponse, MediaListResponse, MediaUpdate, UsefulLink
from app.service.media_service import MediaService
from app.storage.minio import get_presigned_url_from_file_url

router = APIRouter()


def get_media_service(db: AsyncSession = Depends(get_db)) -> MediaService:
    return MediaService(MediaRepository(db))


@router.get("", response_model=MediaListResponse)
async def get_media(
    media_type: MediaType | None = Query(None),
    category: MediaCategory | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    """Список опубликованного обучающего контента."""
    return await service.get_all(
        media_type=media_type,
        category=category,
        offset=offset,
        limit=limit,
    )


@router.get("/{media_id}", response_model=MediaResponse)
async def get_media_item(
    media_id: int,
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    """Получить материал с инструкцией и полезными ссылками."""
    return await service.get_by_id(media_id)


@router.get("/{media_id}/download")
async def get_media_download_url(
    media_id: int,
    expires_minutes: int = Query(60, ge=1, le=24 * 60),
    current_user: User = Depends(get_current_user),
    service: MediaService = Depends(get_media_service),
):
    """Временный URL для просмотра/скачивания файла обучающего материала."""
    media = await service.get_by_id(media_id)
    if not media:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media not found.")
    url = get_presigned_url_from_file_url(media.file_url, expires_minutes)
    return {
        "url": url,
        "file_name": media.file_name,
        "mime_type": media.mime_type,
        "expires_in": expires_minutes * 60,
    }


@router.post("/upload", response_model=MediaResponse, status_code=201)
async def upload_media(
    title: str = Form(...),
    media_type: MediaType = Form(...),
    category: MediaCategory = Form(...),
    file: UploadFile = File(...),
    description: str | None = Form(None),
    instruction: str | None = Form(None, description="Текст инструкции к уроку"),
    useful_links: str | None = Form(
        None,
        description='JSON список ссылок: [{"label": "Сайт", "url": "https://..."}]'
    ),
    current_user: User = Depends(require_admin),
    service: MediaService = Depends(get_media_service),
):
    """Загрузить обучающий материал — только для админов."""
    parsed_links = None
    if useful_links:
        try:
            raw = json.loads(useful_links)
            parsed_links = [UsefulLink(**item) for item in raw]
        except Exception:
            from fastapi import HTTPException
            raise HTTPException(status_code=400, detail="Invalid useful_links format.")

    return await service.upload(
        title=title,
        description=description,
        instruction=instruction,
        useful_links=parsed_links,
        media_type=media_type,
        category=category,
        file=file,
    )


@router.patch("/{media_id}", response_model=MediaResponse)
async def update_media(
    media_id: int,
    data: MediaUpdate,
    current_user: User = Depends(require_admin),
    service: MediaService = Depends(get_media_service),
):
    """Обновить текст, ссылки или статус публикации — только для админов."""
    return await service.update(media_id, data)


@router.delete("/{media_id}", status_code=204)
async def delete_media(
    media_id: int,
    current_user: User = Depends(require_admin),
    service: MediaService = Depends(get_media_service),
):
    """Удалить материал — только для админов."""
    await service.delete(media_id) 