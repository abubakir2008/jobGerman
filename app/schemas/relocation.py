from pydantic import BaseModel
from app.models.relocation import RelocationStage


class RelocationCaseUpdate(BaseModel):
    stage: RelocationStage | None = None
    manager_id: int | None = None
    notes: str | None = None


class RelocationCaseResponse(BaseModel):
    id: int
    application_id: int
    manager_id: int | None
    stage: RelocationStage
    notes: str | None

    model_config = {"from_attributes": True}


class RelocationCaseListResponse(BaseModel):
    items: list[RelocationCaseResponse]
    total: int 