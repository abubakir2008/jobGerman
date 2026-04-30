"""Аналитика для админ-панели: воронка, популярные вакансии, статусы кейсов."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import require_admin
from app.models.application import Application, ApplicationStatus
from app.models.job import Job
from app.models.relocation import RelocationCase, RelocationStage
from app.models.user import CandidateProfile, User, UserRole

router = APIRouter()


@router.get("/stats")
async def admin_stats(
    current_user=Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    # Воронка: пользователи -> с профилем -> с откликом -> принятый -> завершенный кейс
    total_users = await db.scalar(select(func.count(User.id))) or 0
    candidates = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.candidate)
    ) or 0
    managers = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.manager)
    ) or 0
    admins = await db.scalar(
        select(func.count(User.id)).where(User.role == UserRole.admin)
    ) or 0

    profiles = await db.scalar(select(func.count(CandidateProfile.id))) or 0

    total_apps = await db.scalar(select(func.count(Application.id))) or 0
    accepted_apps = await db.scalar(
        select(func.count(Application.id)).where(Application.status == ApplicationStatus.accepted)
    ) or 0
    pending_apps = await db.scalar(
        select(func.count(Application.id)).where(Application.status == ApplicationStatus.pending)
    ) or 0

    total_cases = await db.scalar(select(func.count(RelocationCase.id))) or 0
    completed_cases = await db.scalar(
        select(func.count(RelocationCase.id)).where(
            RelocationCase.stage == RelocationStage.completed
        )
    ) or 0

    # Кейсы по этапам
    stage_rows = await db.execute(
        select(RelocationCase.stage, func.count(RelocationCase.id))
        .group_by(RelocationCase.stage)
    )
    stages_breakdown = [
        {"stage": s.value if hasattr(s, "value") else str(s), "count": c}
        for s, c in stage_rows.all()
    ]

    # Топ-5 вакансий по числу откликов
    top_jobs_rows = await db.execute(
        select(
            Job.id,
            Job.title,
            func.count(Application.id).label("apps"),
        )
        .join(Application, Application.job_id == Job.id, isouter=True)
        .group_by(Job.id, Job.title)
        .order_by(func.count(Application.id).desc())
        .limit(5)
    )
    top_jobs = [
        {"id": j.id, "title": j.title, "applications": j.apps}
        for j in top_jobs_rows.all()
    ]

    # География: топ стран кандидатов
    geo_rows = await db.execute(
        select(CandidateProfile.country, func.count(CandidateProfile.id))
        .where(CandidateProfile.country.is_not(None))
        .group_by(CandidateProfile.country)
        .order_by(func.count(CandidateProfile.id).desc())
        .limit(10)
    )
    geography = [
        {"country": c or "Unknown", "count": cnt}
        for c, cnt in geo_rows.all()
    ]

    funnel = [
        {"step": "Пользователи", "count": total_users},
        {"step": "С профилем", "count": profiles},
        {"step": "Откликнулись", "count": total_apps},
        {"step": "Приняты", "count": accepted_apps},
        {"step": "Завершили переезд", "count": completed_cases},
    ]

    return {
        "totals": {
            "users": total_users,
            "candidates": candidates,
            "managers": managers,
            "admins": admins,
            "profiles": profiles,
            "applications": total_apps,
            "applications_pending": pending_apps,
            "applications_accepted": accepted_apps,
            "cases": total_cases,
            "cases_completed": completed_cases,
        },
        "funnel": funnel,
        "stages": stages_breakdown,
        "top_jobs": top_jobs,
        "geography": geography,
    }
