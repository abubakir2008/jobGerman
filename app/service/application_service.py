from fastapi import HTTPException, status

from app.models.application import ApplicationStatus
from app.repositories.application_repository import ApplicationRepository
from app.schemas.appliction import (
    ApplicationCreate, ApplicationUpdate,
    ApplicationResponse, ApplicationListResponse,
)


class ApplicationService:

    def __init__(self, repo: ApplicationRepository):
        self.repo = repo

    async def get_all(
        self,
        candidate_id: int | None = None,
        job_id: int | None = None,
        status: ApplicationStatus | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> ApplicationListResponse:
        applications, total = await self.repo.get_all(
            candidate_id=candidate_id,
            job_id=job_id,
            status=status,
            offset=offset,
            limit=limit,
        )
        return ApplicationListResponse(
            items=[ApplicationResponse.model_validate(a) for a in applications],
            total=total,
        )

    async def get_by_id(self, application_id: int) -> ApplicationResponse:
        application = await self.repo.get_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found.",
            )
        return ApplicationResponse.model_validate(application)

    async def create(self, candidate_id: int, data: ApplicationCreate) -> ApplicationResponse:
        # Проверяем дубликат
        existing = await self.repo.get_by_candidate_and_job(candidate_id, data.job_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already applied for this job.",
            )
        application = await self.repo.create(candidate_id, data)
        return ApplicationResponse.model_validate(application)

    async def update_status(
        self, application_id: int, data: ApplicationUpdate
    ) -> ApplicationResponse:
        application = await self.repo.get_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found.",
            )
        updated = await self.repo.update(application, data)
        return ApplicationResponse.model_validate(updated)

    async def withdraw(self, application_id: int, candidate_id: int) -> ApplicationResponse:
        application = await self.repo.get_by_id(application_id)
        if not application:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application {application_id} not found.",
            )
        if application.candidate_id != candidate_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only withdraw your own applications.",
            )
        if application.status == ApplicationStatus.withdrawn:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Application is already withdrawn.",
            )
        data = ApplicationUpdate(status=ApplicationStatus.withdrawn)
        updated = await self.repo.update(application, data)
        return ApplicationResponse.model_validate(updated) 