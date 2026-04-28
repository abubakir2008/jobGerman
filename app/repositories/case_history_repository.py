from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_stage_history import CaseStageHistory
from app.models.relocation import RelocationStage


class CaseHistoryRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        case_id: int,
        stage: RelocationStage,
        changed_by_id: int | None,
        note: str | None = None,
    ) -> CaseStageHistory:
        entry = CaseStageHistory(
            case_id=case_id,
            stage=stage,
            changed_by_id=changed_by_id,
            note=note,
        )
        self.db.add(entry)
        await self.db.commit()
        await self.db.refresh(entry)
        return entry

    async def get_by_case(
        self, case_id: int
    ) -> tuple[list[CaseStageHistory], int]:
        query = (
            select(CaseStageHistory)
            .where(CaseStageHistory.case_id == case_id)
            .order_by(CaseStageHistory.changed_at.asc())
        )
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query)
        return result.scalars().all(), total
