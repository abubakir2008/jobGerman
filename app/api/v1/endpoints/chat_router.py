from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user, decode_token
from app.models.user import User, UserRole
from app.repositories.chat_repository import ChatRepository
from app.repositories.relocation_repository import RelocationCaseRepository

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[int, list[tuple[WebSocket, int]]] = {}

    async def connect(self, websocket: WebSocket, case_id: int, user_id: int):
        await websocket.accept()
        self._connections.setdefault(case_id, []).append((websocket, user_id))

    def disconnect(self, websocket: WebSocket, case_id: int):
        conns = self._connections.get(case_id, [])
        self._connections[case_id] = [(ws, uid) for ws, uid in conns if ws != websocket]

    async def broadcast(self, case_id: int, payload: dict, *, exclude: WebSocket | None = None):
        for ws, _ in list(self._connections.get(case_id, [])):
            if exclude is not None and ws is exclude:
                continue
            try:
                await ws.send_json(payload)
            except Exception:
                pass


manager = ConnectionManager()


@router.websocket("/ws/chat/{case_id}")
async def websocket_chat(
    websocket: WebSocket,
    case_id: int,
    token: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    user_id = decode_token(token)
    if not user_id:
        await websocket.close(code=4001)
        return

    case_repo = RelocationCaseRepository(db)
    case = await case_repo.get_by_id(case_id)
    if not case:
        await websocket.close(code=4004)
        return

    candidate_user_id = await case_repo.get_candidate_user_id(case_id)

    # Подгружаем юзера для проверки роли и имени
    user_obj = await db.scalar(select(User).where(User.id == user_id))
    is_admin = user_obj is not None and user_obj.role == UserRole.admin

    if user_id not in (candidate_user_id, case.manager_id) and not is_admin:
        await websocket.close(code=4003)
        return

    sender_name = user_obj.full_name if user_obj else None
    sender_role = user_obj.role.value if user_obj else None

    chat_repo = ChatRepository(db)
    await manager.connect(websocket, case_id, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type", "message")

            if event_type == "typing":
                # Пульс «печатает» — никуда не сохраняем, шлём остальным участникам
                await manager.broadcast(
                    case_id,
                    {
                        "type": "typing",
                        "sender_id": user_id,
                        "sender_name": sender_name,
                    },
                    exclude=websocket,
                )
                continue

            text = (data.get("message") or "").strip()
            if not text:
                continue

            msg = await chat_repo.create(case_id=case_id, sender_id=user_id, message=text)
            await manager.broadcast(case_id, {
                "type": "message",
                "id": msg.id,
                "sender_id": user_id,
                "sender_name": sender_name,
                "sender_role": sender_role,
                "message": text,
                "created_at": msg.created_at.isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, case_id)


@router.get("/chat/{case_id}/messages")
async def get_messages(
    case_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_repo = ChatRepository(db)
    items, total = await chat_repo.get_by_case(case_id, offset, limit)

    # Подгружаем имена отправителей одним запросом
    name_map: dict[int, tuple[str | None, str | None]] = {}
    sender_ids = list({m.sender_id for m in items})
    if sender_ids:
        rows = await db.execute(
            select(User.id, User.full_name, User.role).where(User.id.in_(sender_ids))
        )
        for row in rows.all():
            name_map[row.id] = (row.full_name, row.role.value)

    return {
        "items": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "sender_name": name_map.get(m.sender_id, (None, None))[0],
                "sender_role": name_map.get(m.sender_id, (None, None))[1],
                "message": m.message,
                "is_read": m.is_read,
                "created_at": m.created_at.isoformat(),
            }
            for m in items
        ],
        "total": total,
    }


@router.post("/chat/{case_id}/messages/read")
async def mark_read(
    case_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_repo = ChatRepository(db)
    await chat_repo.mark_all_read(case_id=case_id, reader_id=current_user.id)
    return {"ok": True}
