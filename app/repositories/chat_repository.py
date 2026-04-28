from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chat_message import ChatMessage


class ChatRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, case_id: int, sender_id: int, message: str) -> ChatMessage:
        msg = ChatMessage(case_id=case_id, sender_id=sender_id, message=message)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_by_case(
        self, case_id: int, offset: int = 0, limit: int = 50
    ) -> tuple[list[ChatMessage], int]:
        query = (
            select(ChatMessage)
            .where(ChatMessage.case_id == case_id)
            .order_by(ChatMessage.created_at.asc())
        )
        total = await self.db.scalar(select(func.count()).select_from(query.subquery()))
        result = await self.db.execute(query.offset(offset).limit(limit))
        return result.scalars().all(), total

    async def mark_all_read(self, case_id: int, reader_id: int) -> None:
        await self.db.execute(
            update(ChatMessage)
            .where(ChatMessage.case_id == case_id, ChatMessage.sender_id != reader_id)
            .values(is_read=True)
        )
        await self.db.commit()

    async def unread_count(self, case_id: int, reader_id: int) -> int:
        result = await self.db.scalar(
            select(func.count())
            .where(
                ChatMessage.case_id == case_id,
                ChatMessage.sender_id != reader_id,
                ChatMessage.is_read == False,  # noqa: E712
            )
        )
        return result or 0
