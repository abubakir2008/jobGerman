from datetime import date, datetime
from pydantic import BaseModel
from app.models.relocation import RelocationStage


class CandidateShort(BaseModel):
    id: int
    full_name: str
    email: str
    phone: str | None = None

    model_config = {"from_attributes": True}


class ManagerShort(BaseModel):
    id: int
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class RelocationCaseUpdate(BaseModel):
    stage: RelocationStage | None = None
    manager_id: int | None = None
    notes: str | None = None
    stage_deadline: date | None = None


class RelocationCaseResponse(BaseModel):
    id: int
    application_id: int
    manager_id: int | None
    stage: RelocationStage
    notes: str | None
    stage_deadline: date | None = None
    # Расширения — чтобы UI показывал имена, а не номера
    candidate: CandidateShort | None = None
    manager: ManagerShort | None = None
    job_title: str | None = None

    model_config = {"from_attributes": True}


class RelocationCaseListResponse(BaseModel):
    items: list[RelocationCaseResponse]
    total: int


class AdvanceStageRequest(BaseModel):
    confirm: bool = False


class StageRequirement(BaseModel):
    key: str
    label: str
    done: bool


class StageRequirementsResponse(BaseModel):
    current_stage: RelocationStage
    next_stage: RelocationStage | None
    can_advance: bool
    requirements: list[StageRequirement]


class CaseHistoryItem(BaseModel):
    id: int
    case_id: int
    stage: RelocationStage
    changed_by_id: int | None
    changed_by_name: str | None = None
    changed_at: datetime
    note: str | None

    model_config = {"from_attributes": True}


class CaseHistoryResponse(BaseModel):
    items: list[CaseHistoryItem]
    total: int
