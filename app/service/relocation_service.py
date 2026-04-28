from fastapi import HTTPException, status

from app.models.document import DocumentType
from app.models.notification import NotificationType
from app.models.relocation import RelocationStage
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
    StageRequirement,
    StageRequirementsResponse,
)

STAGE_TRANSITIONS = {
    RelocationStage.applied:    RelocationStage.interview,
    RelocationStage.interview:  RelocationStage.documents,
    RelocationStage.documents:  RelocationStage.visa,
    RelocationStage.visa:       RelocationStage.relocation,
    RelocationStage.relocation: RelocationStage.completed,
    RelocationStage.completed:  None,
}

# Документы, обязательные для каждого целевого этапа
STAGE_REQUIRED_DOCS: dict[RelocationStage, list[tuple[DocumentType, str]]] = {
    RelocationStage.visa: [
        (DocumentType.passport, "Паспорт"),
        (DocumentType.cv, "CV"),
        (DocumentType.diploma, "Диплом"),
    ],
    RelocationStage.relocation: [
        (DocumentType.visa, "Виза"),
    ],
}


class RelocationCaseService:

    def __init__(
        self,
        repo: RelocationCaseRepository,
        doc_repo: DocumentRepository,
        history_repo: CaseHistoryRepository,
        notif_repo: NotificationRepository,
    ):
        self.repo = repo
        self.doc_repo = doc_repo
        self.history_repo = history_repo
        self.notif_repo = notif_repo

    async def get_all(
        self,
        manager_id: int | None = None,
        stage: RelocationStage | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> RelocationCaseListResponse:
        cases, total = await self.repo.get_all(
            manager_id=manager_id, stage=stage, offset=offset, limit=limit
        )
        return RelocationCaseListResponse(
            items=[RelocationCaseResponse.model_validate(c) for c in cases],
            total=total,
        )

    async def get_by_id(self, case_id: int) -> RelocationCaseResponse:
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")
        return RelocationCaseResponse.model_validate(case)

    async def get_by_application(self, application_id: int) -> RelocationCaseResponse:
        case = await self.repo.get_by_application_id(application_id)
        if not case:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                detail=f"Case for application {application_id} not found.",
            )
        return RelocationCaseResponse.model_validate(case)

    async def update(self, case_id: int, data: RelocationCaseUpdate) -> RelocationCaseResponse:
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")

        if data.stage and data.stage != case.stage:
            allowed_next = STAGE_TRANSITIONS.get(case.stage)
            if data.stage != allowed_next:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid stage transition: {case.stage} → {data.stage}. Expected: {allowed_next}.",
                )

        updated = await self.repo.update(case, data)
        return RelocationCaseResponse.model_validate(updated)

    async def get_requirements(self, case_id: int) -> StageRequirementsResponse:
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")

        next_stage = STAGE_TRANSITIONS.get(case.stage)
        requirements: list[StageRequirement] = []

        if next_stage == RelocationStage.interview:
            app_status = await self.repo.get_application_status(case_id)
            from app.models.application import ApplicationStatus
            done = app_status in (ApplicationStatus.reviewing, ApplicationStatus.accepted)
            requirements.append(StageRequirement(
                key="application_status", label="Заявка на рассмотрении", done=done
            ))

        elif next_stage == RelocationStage.documents:
            done = bool(case.notes and case.notes.strip())
            requirements.append(StageRequirement(
                key="interview_note", label="Заметка менеджера (подтверждение интервью)", done=done
            ))

        elif next_stage in STAGE_REQUIRED_DOCS:
            user_id = await self.repo.get_candidate_user_id(case_id)
            uploaded = await self.doc_repo.get_doc_types_for_user(user_id) if user_id else set()
            for doc_type, label in STAGE_REQUIRED_DOCS[next_stage]:
                requirements.append(StageRequirement(
                    key=doc_type.value, label=label, done=doc_type in uploaded
                ))

        elif next_stage == RelocationStage.completed:
            requirements.append(StageRequirement(
                key="confirm", label="Явное подтверждение менеджера", done=False
            ))

        can_advance = bool(next_stage) and all(r.done for r in requirements)
        return StageRequirementsResponse(
            current_stage=case.stage,
            next_stage=next_stage,
            can_advance=can_advance,
            requirements=requirements,
        )

    async def advance_stage(
        self, case_id: int, manager_id: int, request: AdvanceStageRequest
    ) -> RelocationCaseResponse:
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")

        next_stage = STAGE_TRANSITIONS.get(case.stage)
        if not next_stage:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Case is already completed.")

        # --- Gate checks ---
        await self._check_gate(case_id, case, next_stage, request)

        # Применяем переход
        data = RelocationCaseUpdate(stage=next_stage)
        updated = await self.repo.update(case, data)

        # Записываем историю
        await self.history_repo.create(
            case_id=case_id,
            stage=next_stage,
            changed_by_id=manager_id,
            note=case.notes,
        )

        # Уведомляем кандидата
        user_id = await self.repo.get_candidate_user_id(case_id)
        if user_id:
            await self.notif_repo.create(
                user_id=user_id,
                type=NotificationType.stage_change,
                message=f"Ваш кейс перешёл на этап: {next_stage.value}",
            )

        return RelocationCaseResponse.model_validate(updated)

    async def _check_gate(self, case_id, case, next_stage, request: AdvanceStageRequest):
        if next_stage == RelocationStage.interview:
            app_status = await self.repo.get_application_status(case_id)
            from app.models.application import ApplicationStatus
            if app_status not in (ApplicationStatus.reviewing, ApplicationStatus.accepted):
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Application must be in 'reviewing' or 'accepted' status.",
                )

        elif next_stage == RelocationStage.documents:
            if not case.notes or not case.notes.strip():
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Manager must add a note confirming the interview before advancing.",
                )

        elif next_stage in STAGE_REQUIRED_DOCS:
            user_id = await self.repo.get_candidate_user_id(case_id)
            uploaded = await self.doc_repo.get_doc_types_for_user(user_id) if user_id else set()
            missing = [
                label for doc_type, label in STAGE_REQUIRED_DOCS[next_stage]
                if doc_type not in uploaded
            ]
            if missing:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=f"Required documents missing: {', '.join(missing)}",
                )

        elif next_stage == RelocationStage.completed:
            if not request.confirm:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail="Explicit confirmation required. Send { \"confirm\": true }.",
                )

    async def get_history(self, case_id: int) -> CaseHistoryResponse:
        case = await self.repo.get_by_id(case_id)
        if not case:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Case {case_id} not found.")
        items, total = await self.history_repo.get_by_case(case_id)
        from app.schemas.relocation import CaseHistoryItem
        return CaseHistoryResponse(
            items=[CaseHistoryItem.model_validate(i) for i in items],
            total=total,
        )
