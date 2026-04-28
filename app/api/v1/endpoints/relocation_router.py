from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user, require_manager
from app.models.relocation import RelocationStage
from app.models.user import User
from app.repositories.case_history_repository import CaseHistoryRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.relocation_repository import RelocationCaseRepository
from app.schemas.relocation import (
    AdvanceStageRequest,
    CaseHistoryResponse,
    RelocationCaseListResponse,
    RelocationCaseResponse,
    RelocationCaseUpdate,
    StageRequirementsResponse,
)
from app.service.relocation_service import RelocationCaseService

router = APIRouter()


def get_relocation_service(db: AsyncSession = Depends(get_db)) -> RelocationCaseService:
    return RelocationCaseService(
        RelocationCaseRepository(db),
        DocumentRepository(db),
        CaseHistoryRepository(db),
        NotificationRepository(db),
    )


@router.get("", response_model=RelocationCaseListResponse)
async def get_cases(
    stage: RelocationStage | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_all(stage=stage, offset=offset, limit=limit)


@router.get("/my", response_model=RelocationCaseListResponse)
async def get_my_cases(
    stage: RelocationStage | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_all(manager_id=current_user.id, stage=stage, offset=offset, limit=limit)


@router.get("/by-application/{application_id}", response_model=RelocationCaseResponse)
async def get_case_by_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_by_application(application_id)


@router.get("/{case_id}", response_model=RelocationCaseResponse)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_by_id(case_id)


@router.get("/{case_id}/requirements", response_model=StageRequirementsResponse)
async def get_requirements(
    case_id: int,
    current_user: User = Depends(get_current_user),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_requirements(case_id)


@router.get("/{case_id}/history", response_model=CaseHistoryResponse)
async def get_history(
    case_id: int,
    current_user: User = Depends(get_current_user),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_history(case_id)


@router.patch("/{case_id}", response_model=RelocationCaseResponse)
async def update_case(
    case_id: int,
    data: RelocationCaseUpdate,
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.update(case_id, data)


@router.post("/{case_id}/advance", response_model=RelocationCaseResponse)
async def advance_stage(
    case_id: int,
    request: AdvanceStageRequest = AdvanceStageRequest(),
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.advance_stage(case_id, current_user.id, request)
