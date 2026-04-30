from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.relocation import RelocationCase, RelocationStage
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.user import CandidateProfile, User
from app.schemas.relocation import RelocationCaseUpdate


class RelocationCaseRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(
        self,
        manager_id: int | None = None,
        stage: RelocationStage | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[RelocationCase], int]:
        query = select(RelocationCase)

        if manager_id:
            query = query.where(RelocationCase.manager_id == manager_id)
        if stage:
            query = query.where(RelocationCase.stage == stage)

        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def get_by_id(self, case_id: int) -> RelocationCase | None:
        result = await self.db.execute(
            select(RelocationCase).where(RelocationCase.id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_by_application_id(self, application_id: int) -> RelocationCase | None:
        result = await self.db.execute(
            select(RelocationCase).where(RelocationCase.application_id == application_id)
        )
        return result.scalar_one_or_none()

    async def update(self, case: RelocationCase, data: RelocationCaseUpdate) -> RelocationCase:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(case, field, value)
        await self.db.commit()
        await self.db.refresh(case)
        return case

    async def get_application_status(self, case_id: int) -> ApplicationStatus | None:
        """Статус заявки для данного кейса."""
        result = await self.db.execute(
            select(Application.status)
            .join(RelocationCase, Application.id == RelocationCase.application_id)
            .where(RelocationCase.id == case_id)
        )
        return result.scalar_one_or_none()

    async def get_candidate_user_id(self, case_id: int) -> int | None:
        """user_id кандидата для данного кейса."""
        result = await self.db.execute(
            select(Application.candidate_id)
            .join(RelocationCase, Application.id == RelocationCase.application_id)
            .where(RelocationCase.id == case_id)
        )
        return result.scalar_one_or_none()

    # ── Обогащённые выборки: с именем кандидата, менеджера, названием вакансии ──

    async def get_enriched_by_id(self, case_id: int) -> dict | None:
        rows = await self._fetch_enriched(where_clause=RelocationCase.id == case_id)
        return rows[0] if rows else None

    async def get_enriched_by_application_id(self, application_id: int) -> dict | None:
        rows = await self._fetch_enriched(
            where_clause=RelocationCase.application_id == application_id,
        )
        return rows[0] if rows else None

    async def get_enriched_list(
        self,
        manager_id: int | None = None,
        stage: RelocationStage | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[dict], int]:
        count_q = select(func.count(RelocationCase.id))
        if manager_id:
            count_q = count_q.where(RelocationCase.manager_id == manager_id)
        if stage:
            count_q = count_q.where(RelocationCase.stage == stage)
        total = await self.db.scalar(count_q) or 0

        rows = await self._fetch_enriched(
            manager_id=manager_id, stage=stage, offset=offset, limit=limit,
        )
        return rows, total

    async def _fetch_enriched(
        self,
        *,
        where_clause=None,
        manager_id: int | None = None,
        stage: RelocationStage | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict]:
        Manager = aliased(User)

        query = (
            select(
                RelocationCase,
                User.id.label("candidate_user_id"),
                User.full_name.label("candidate_name"),
                User.email.label("candidate_email"),
                CandidateProfile.phone.label("candidate_phone"),
                Manager.id.label("manager_user_id"),
                Manager.full_name.label("manager_name"),
                Manager.email.label("manager_email"),
                Job.title.label("job_title"),
            )
            .join(Application, Application.id == RelocationCase.application_id)
            .join(User, User.id == Application.candidate_id)
            .outerjoin(CandidateProfile, CandidateProfile.user_id == User.id)
            .join(Job, Job.id == Application.job_id)
            .outerjoin(Manager, Manager.id == RelocationCase.manager_id)
        )

        if where_clause is not None:
            query = query.where(where_clause)
        if manager_id:
            query = query.where(RelocationCase.manager_id == manager_id)
        if stage:
            query = query.where(RelocationCase.stage == stage)

        query = query.order_by(RelocationCase.id.desc()).offset(offset).limit(limit)
        result = await self.db.execute(query)

        items: list[dict] = []
        for row in result.all():
            case: RelocationCase = row[0]
            items.append({
                "case": case,
                "candidate": {
                    "id": row.candidate_user_id,
                    "full_name": row.candidate_name,
                    "email": row.candidate_email,
                    "phone": row.candidate_phone,
                },
                "manager": (
                    {
                        "id": row.manager_user_id,
                        "full_name": row.manager_name,
                        "email": row.manager_email,
                    }
                    if row.manager_user_id is not None
                    else None
                ),
                "job_title": row.job_title,
            })
        return items
