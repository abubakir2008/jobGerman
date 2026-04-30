from pydantic import BaseModel
from app.models.application import ApplicationStatus
from app.models.relocation import RelocationStage


class ApplicationCreate(BaseModel):
    job_id: int
    cover_letter: str | None = None
    cv_document_id: int | None = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus


class RelocationCaseShort(BaseModel):
    id: int
    stage: RelocationStage
    manager_id: int | None

    model_config = {"from_attributes": True}


class CvDocumentShort(BaseModel):
    id: int
    file_name: str
    mime_type: str | None = None

    model_config = {"from_attributes": True}


class ApplicationResponse(BaseModel):
    id: int
    candidate_id: int
    job_id: int
    status: ApplicationStatus
    cover_letter: str | None
    cv_document_id: int | None = None
    cv_document: CvDocumentShort | None = None
    relocation_case: RelocationCaseShort | None = None

    model_config = {"from_attributes": True}


class ApplicationListResponse(BaseModel):
    items: list[ApplicationResponse]
    total: int
