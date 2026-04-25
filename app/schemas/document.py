from pydantic import BaseModel
from app.models.document import DocumentType


class DocumentResponse(BaseModel):
    id: int
    candidate_id: int
    doc_type: DocumentType
    file_name: str
    file_url: str
    file_size: int | None
    mime_type: str | None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int 