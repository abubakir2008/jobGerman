from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user, require_manager
from app.models.relocation import RelocationStage
from app.models.user import User
from app.repositories.relocation_repository import RelocationCaseRepository
from app.schemas.relocation import (
    RelocationCaseUpdate,
    RelocationCaseResponse,
    RelocationCaseListResponse,
)
from app.service.relocation_service import RelocationCaseService

router = APIRouter()


def get_relocation_service(db: AsyncSession = Depends(get_db)) -> RelocationCaseService:
    return RelocationCaseService(RelocationCaseRepository(db))


@router.get("", response_model=RelocationCaseListResponse)
async def get_cases(
    stage: RelocationStage | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    """Список всех кейсов — только для менеджеров и админов."""
    return await service.get_all(
        manager_id=None,  # админ видит все, можно добавить фильтр
        stage=stage,
        offset=offset,
        limit=limit,
    )


@router.get("/my", response_model=RelocationCaseListResponse)
async def get_my_cases(
    stage: RelocationStage | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    """Кейсы назначенные на текущего менеджера."""
    return await service.get_all(
        manager_id=current_user.id,
        stage=stage,
        offset=offset,
        limit=limit,
    )


@router.get("/{case_id}", response_model=RelocationCaseResponse)
async def get_case(
    case_id: int,
    current_user: User = Depends(get_current_user),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_by_id(case_id)


@router.get("/by-application/{application_id}", response_model=RelocationCaseResponse)
async def get_case_by_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    return await service.get_by_application(application_id)


@router.patch("/{case_id}", response_model=RelocationCaseResponse)
async def update_case(
    case_id: int,
    data: RelocationCaseUpdate,
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    """Обновить этап, менеджера или заметки."""
    return await service.update(case_id, data)


@router.post("/{case_id}/advance", response_model=RelocationCaseResponse)
async def advance_stage(
    case_id: int,
    current_user: User = Depends(require_manager),
    service: RelocationCaseService = Depends(get_relocation_service),
):
    """Перейти на следующий этап одной кнопкой."""
    return await service.advance_stage(case_id) 