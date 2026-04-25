from fastapi import HTTPException, status

from app.models.relocation import RelocationStage
from app.repositories.relocation_repository import RelocationCaseRepository
from app.schemas.relocation import (
    RelocationCaseUpdate,
    RelocationCaseResponse,
    RelocationCaseListResponse,
)

# Допустимые переходы между этапами
STAGE_TRANSITIONS = {
    RelocationStage.applied:    RelocationStage.interview,
    RelocationStage.interview:  RelocationStage.documents,
    RelocationStage.documents:  RelocationStage.visa,
    RelocationStage.visa:       RelocationStage.relocation,
    RelocationStage.relocation: RelocationStage.completed,
    RelocationStage.completed:  None,
}


class RelocationCaseService:

    def __init__(self, repo: RelocationCaseRepository):
        self.repo = repo

    async def get_all(
        self,
        manager_id: int | None = None,
        stage: RelocationStage | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> RelocationCaseListResponse:
        cases, total = await self.repo.get_all(
            manager_id=manager_id,
            stage=stage,
            offset=offset,
            limit=limit,
        )
        return RelocationCaseListResponse(
            items=[RelocationCaseResponse.model_validate(c) for c in cases],
            total=total,
        )

    async def get_by_id(self, case_id: int) -> RelocationCaseResponse:
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relocation case {case_id} not found.",
            )
        return RelocationCaseResponse.model_validate(case)

    async def get_by_application(self, application_id: int) -> RelocationCaseResponse:
        case = await self.repo.get_by_application_id(application_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relocation case for application {application_id} not found.",
            )
        return RelocationCaseResponse.model_validate(case)

    async def update(self, case_id: int, data: RelocationCaseUpdate) -> RelocationCaseResponse:
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relocation case {case_id} not found.",
            )

        # Проверяем что переход между этапами допустимый
        if data.stage and data.stage != case.stage:
            allowed_next = STAGE_TRANSITIONS.get(case.stage)
            if data.stage != allowed_next:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Invalid stage transition: {case.stage} → {data.stage}. "
                        f"Expected next stage: {allowed_next}."
                    ),
                )

        updated = await self.repo.update(case, data)
        return RelocationCaseResponse.model_validate(updated)

    async def advance_stage(self, case_id: int) -> RelocationCaseResponse:
        """Переход на следующий этап одной кнопкой."""
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Relocation case {case_id} not found.",
            )

        next_stage = STAGE_TRANSITIONS.get(case.stage)
        if not next_stage:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Case is already completed.",
            )

        data = RelocationCaseUpdate(stage=next_stage)
        updated = await self.repo.update(case, data)
        return RelocationCaseResponse.model_validate(updated) 