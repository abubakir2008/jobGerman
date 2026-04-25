from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.dependencies.auth import get_current_user
from app.models.application import ApplicationStatus
from app.models.user import User
from app.repositories.application_repository import ApplicationRepository
from app.schemas.appliction import (
    ApplicationCreate, ApplicationUpdate,
    ApplicationResponse, ApplicationListResponse,
)
from app.service.application_service import ApplicationService

router = APIRouter()


def get_application_service(db: AsyncSession = Depends(get_db)) -> ApplicationService:
    return ApplicationService(ApplicationRepository(db))


@router.get("", response_model=ApplicationListResponse)
async def get_applications(
    job_id: int | None = Query(None),
    status: ApplicationStatus | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
):
    # Кандидат видит только свои отклики
    candidate_id = current_user.id
    return await service.get_all(
        candidate_id=candidate_id,
        job_id=job_id,
        status=status,
        offset=offset,
        limit=limit,
    )


@router.get("/{application_id}", response_model=ApplicationResponse)
async def get_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
):
    return await service.get_by_id(application_id)


@router.post("", response_model=ApplicationResponse, status_code=201)
async def create_application(
    data: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
):
    # RelocationCase создаётся автоматически в репозитории
    return await service.create(current_user.id, data)


@router.patch("/{application_id}/status", response_model=ApplicationResponse)
async def update_application_status(
    application_id: int,
    data: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
):
    return await service.update_status(application_id, data)


@router.post("/{application_id}/withdraw", response_model=ApplicationResponse)
async def withdraw_application(
    application_id: int,
    current_user: User = Depends(get_current_user),
    service: ApplicationService = Depends(get_application_service),
):
    return await service.withdraw(application_id, current_user.id) 