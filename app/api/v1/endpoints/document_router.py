from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.document import DocumentType
from app.models.user import User, UserRole
from app.repositories.document_repository import DocumentRepository
from app.repositories.profeli_repository import ProfileRepository
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.service.document_service import DocumentService
from app.storage.minio import get_presigned_url_from_file_url

router = APIRouter()


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(DocumentRepository(db), ProfileRepository(db))


def get_document_repo(db: AsyncSession = Depends(get_db)) -> DocumentRepository:
    return DocumentRepository(db)


@router.get("", response_model=DocumentListResponse)
async def get_documents(
    doc_type: DocumentType | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.get_all(current_user.id, doc_type)


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    doc_type: DocumentType = Query(..., description="passport / cv / diploma / translation / other"),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    return await service.upload(current_user.id, doc_type, file)


@router.get("/{document_id}/download")
async def get_document_download_url(
    document_id: int,
    expires_minutes: int = Query(60, ge=1, le=24 * 60),
    current_user: User = Depends(get_current_user),
    repo: DocumentRepository = Depends(get_document_repo),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает временный URL (presigned) для просмотра/скачивания файла из MinIO.

    Доступно владельцу документа, а также менеджеру/админу.
    """
    document = await repo.get_by_id(document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

    # Проверка прав: владелец (через candidate_profile) или manager/admin
    if current_user.role not in (UserRole.manager, UserRole.admin):
        from sqlalchemy import select
        from app.models.user import CandidateProfile
        owner = await db.scalar(
            select(CandidateProfile.user_id).where(CandidateProfile.id == document.candidate_id)
        )
        if owner != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own documents.",
            )

    url = get_presigned_url_from_file_url(document.file_url, expires_minutes)
    return {
        "url": url,
        "file_name": document.file_name,
        "mime_type": document.mime_type,
        "expires_in": expires_minutes * 60,
    }


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    await service.delete(current_user.id, document_id)
