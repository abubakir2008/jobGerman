from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.config import settings
from app.config.rate_limit import RateLimitMiddleware
from app.api.v1.endpoints.router import router
from app.storage.minio import ensure_bucket_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_bucket_exists()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting (in-memory, по IP). 60 req/min для всех путей,
# 10 req/min — для /auth/login и /auth/register.
app.add_middleware(
    RateLimitMiddleware,
    default_per_minute=120,
    auth_per_minute=10,
)

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}