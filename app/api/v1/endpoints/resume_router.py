from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.resume import Resume
from app.models.user import User, UserRole
from app.schemas.resume import ResumeResponse, ResumeUpsert

router = APIRouter()


async def _get_for_user(db: AsyncSession, user_id: int) -> Resume | None:
    return await db.scalar(select(Resume).where(Resume.user_id == user_id))


def _to_dict(payload: ResumeUpsert) -> dict:
    data = payload.model_dump()
    # Pydantic-модели → plain JSON для JSONB
    for key in ("experience", "projects", "education", "languages", "extras"):
        data[key] = [v if isinstance(v, dict) else v for v in (data.get(key) or [])]
    return data


@router.get("/me", response_model=ResumeResponse)
async def get_my_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_for_user(db, current_user.id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return resume


@router.put("/me", response_model=ResumeResponse)
async def upsert_my_resume(
    data: ResumeUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    resume = await _get_for_user(db, current_user.id)
    payload = _to_dict(data)
    if resume:
        for k, v in payload.items():
            setattr(resume, k, v)
    else:
        resume = Resume(user_id=current_user.id, **payload)
        db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("/user/{user_id}", response_model=ResumeResponse)
async def get_user_resume(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Просмотр чужого резюме — только manager/admin."""
    if current_user.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can view other resumes.",
        )
    resume = await _get_for_user(db, user_id)
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found.")
    return resume
