import uuid

from fastapi import HTTPException, UploadFile, status

from app.models.document import DocumentType
from app.repositories.document_repository import DocumentRepository
from app.repositories.profeli_repository import ProfileRepository
from app.schemas.document import DocumentResponse, DocumentListResponse
from app.storage.minio import upload_file, delete_file

# Разрешённые типы файлов
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class DocumentService:

    def __init__(self, doc_repo: DocumentRepository, profile_repo: ProfileRepository):
        self.doc_repo = doc_repo
        self.profile_repo = profile_repo

    async def get_all(
        self,
        user_id: int,
        doc_type: DocumentType | None = None,
    ) -> DocumentListResponse:
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found.",
            )
        documents, total = await self.doc_repo.get_all(profile.id, doc_type)
        return DocumentListResponse(
            items=[DocumentResponse.model_validate(d) for d in documents],
            total=total,
        )

    async def upload(
        self,
        user_id: int,
        doc_type: DocumentType,
        file: UploadFile,
    ) -> DocumentResponse:
        # Проверяем профиль
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found. Create your profile first.",
            )

        # Проверяем тип файла
        if file.content_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not allowed. Allowed: PDF, JPEG, PNG, WEBP.",
            )

        # Читаем файл и проверяем размер
        file_data = await file.read()
        if len(file_data) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large. Maximum size is 10 MB.",
            )

        # Генерируем уникальное имя и загружаем в MinIO
        ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "bin"
        object_name = f"documents/{user_id}/{doc_type}/{uuid.uuid4()}.{ext}"
        file_url = upload_file(file_data, object_name, file.content_type)

        # Сохраняем в БД
        document = await self.doc_repo.create(
            candidate_id=profile.id,
            doc_type=doc_type,
            file_name=file.filename,
            file_url=file_url,
            file_size=len(file_data),
            mime_type=file.content_type,
        )
        return DocumentResponse.model_validate(document)

    async def delete(self, user_id: int, document_id: int) -> None:
        profile = await self.profile_repo.get_by_user_id(user_id)
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profile not found.",
            )

        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found.",
            )

        # Проверяем что документ принадлежит этому кандидату
        if document.candidate_id != profile.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own documents.",
            )

        # Удаляем из MinIO
        try:
            object_name = document.file_url.split("/", 3)[-1]
            delete_file(object_name)
        except Exception:
            pass  # если файл уже удалён из MinIO — не блокируем удаление из БД

        await self.doc_repo.delete(document) 