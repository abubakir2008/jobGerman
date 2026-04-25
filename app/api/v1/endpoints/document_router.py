from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.document import DocumentType
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.repositories.profeli_repository import ProfileRepository
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.service.document_service import DocumentService

router = APIRouter()


def get_document_service(db: AsyncSession = Depends(get_db)) -> DocumentService:
    return DocumentService(DocumentRepository(db), ProfileRepository(db))


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


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    service: DocumentService = Depends(get_document_service),
):
    await service.delete(current_user.id, document_id)