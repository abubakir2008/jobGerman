from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.case_stage_history import CaseStageHistory
from app.models.relocation import RelocationStage
from app.models.user import User


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

    async def get_by_case(self, case_id: int) -> tuple[list[dict], int]:
        """Возвращает историю с подгруженным именем автора изменения."""
        query = (
            select(
                CaseStageHistory,
                User.full_name.label("changed_by_name"),
            )
            .outerjoin(User, User.id == CaseStageHistory.changed_by_id)
            .where(CaseStageHistory.case_id == case_id)
            .order_by(CaseStageHistory.changed_at.asc())
        )
        total = await self.db.scalar(
            select(func.count(CaseStageHistory.id)).where(CaseStageHistory.case_id == case_id)
        ) or 0
        result = await self.db.execute(query)
        items: list[dict] = []
        for row in result.all():
            entry: CaseStageHistory = row[0]
            items.append({
                "id": entry.id,
                "case_id": entry.case_id,
                "stage": entry.stage,
                "changed_by_id": entry.changed_by_id,
                "changed_by_name": row.changed_by_name,
                "changed_at": entry.changed_at,
                "note": entry.note,
            })
        return items, total
