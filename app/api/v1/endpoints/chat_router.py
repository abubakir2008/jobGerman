from datetime import datetime
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user, decode_token
from app.models.user import User
from app.repositories.chat_repository import ChatRepository
from app.repositories.relocation_repository import RelocationCaseRepository

router = APIRouter()


class ConnectionManager:
    def __init__(self):
        # case_id -> list of (websocket, user_id)
        self._connections: dict[int, list[tuple[WebSocket, int]]] = {}

    async def connect(self, websocket: WebSocket, case_id: int, user_id: int):
        await websocket.accept()
        self._connections.setdefault(case_id, []).append((websocket, user_id))

    def disconnect(self, websocket: WebSocket, case_id: int):
        conns = self._connections.get(case_id, [])
        self._connections[case_id] = [(ws, uid) for ws, uid in conns if ws != websocket]

    async def broadcast(self, case_id: int, payload: dict):
        for ws, _ in self._connections.get(case_id, []):
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
    if user_id not in (candidate_user_id, case.manager_id):
        await websocket.close(code=4003)
        return

    chat_repo = ChatRepository(db)
    await manager.connect(websocket, case_id, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("message", "").strip()
            if not text:
                continue

            msg = await chat_repo.create(case_id=case_id, sender_id=user_id, message=text)
            await manager.broadcast(case_id, {
                "id": msg.id,
                "sender_id": user_id,
                "message": text,
                "created_at": msg.created_at.isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, case_id)


@router.get("/chat/{case_id}/messages")
async def get_messages(
    case_id: int,
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat_repo = ChatRepository(db)
    items, total = await chat_repo.get_by_case(case_id, offset, limit)
    return {
        "items": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
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
