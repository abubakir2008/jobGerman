from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentType


class DocumentRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        candidate_id: int,
        doc_type: DocumentType | None = None,
    ) -> tuple[list[Document], int]:
        query = select(Document).where(Document.candidate_id == candidate_id)

        if doc_type:
            query = query.where(Document.doc_type == doc_type)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_by_id(self, document_id: int) -> Document | None:
        result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        candidate_id: int,
        doc_type: DocumentType,
        file_name: str,
        file_url: str,
        file_size: int | None,
        mime_type: str | None,
    ) -> Document:
        document = Document(
            candidate_id=candidate_id,
            doc_type=doc_type,
            file_name=file_name,
            file_url=file_url,
            file_size=file_size,
            mime_type=mime_type,
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        await self.db.delete(document)
        await self.db.commit() 