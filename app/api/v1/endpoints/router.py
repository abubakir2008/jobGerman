from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth_router,
    job_router,
    profile_router,
    application_router,
    relocation_router,
    document_router,
    media_router,
    user_router,
    chat_router,
    notification_router,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth_router.router,          prefix="/auth",          tags=["Auth"])
router.include_router(job_router.router,            prefix="/jobs",          tags=["Jobs"])
router.include_router(profile_router.router,        prefix="/profile",       tags=["Profile"])
router.include_router(application_router.router,    prefix="/applications",  tags=["Applications"])
router.include_router(relocation_router.router,     prefix="/cases",         tags=["Relocation Cases"])
router.include_router(document_router.router,       prefix="/documents",     tags=["Documents"])
router.include_router(media_router.router,          prefix="/media",         tags=["Media"])
router.include_router(user_router.router,           prefix="/users",         tags=["Users (Admin)"])
router.include_router(chat_router.router,           prefix="",               tags=["Chat"])
router.include_router(notification_router.router,   prefix="/notifications", tags=["Notifications"])
