"""Простой in-memory rate limiter (без Redis/slowapi).

Используется как FastAPI Middleware для публичных эндпойнтов.
Достаточно для базовой защиты от DDoS на dev/staging. Для production —
лучше заменить на slowapi+Redis или nginx-уровневый лимит.
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Лимит запросов по IP на чувствительные пути.

    По умолчанию: 60 запросов в минуту на IP. Для /auth/login и /auth/register —
    более жёсткий лимит: 10 запросов в минуту на IP.
    """

    def __init__(self, app, *, default_per_minute: int = 60, auth_per_minute: int = 10):
        super().__init__(app)
        self.default_limit = default_per_minute
        self.auth_limit = auth_per_minute
        self._buckets: dict[str, deque[float]] = defaultdict(deque)

    def _limit_for(self, path: str) -> int:
        if path.startswith("/api/v1/auth/login") or path.startswith("/api/v1/auth/register"):
            return self.auth_limit
        return self.default_limit

    async def dispatch(self, request: Request, call_next):
        # WS-соединения не лимитим (там свой keep-alive)
        if request.scope.get("type") != "http":
            return await call_next(request)

        path = request.url.path
        # Не лимитим OPTIONS (CORS preflight) и health
        if request.method == "OPTIONS" or path in ("/health", "/openapi.json", "/docs", "/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "anonymous"
        key = f"{client_ip}:{self._limit_for(path)}"

        now = time.time()
        window_start = now - 60.0
        bucket = self._buckets[key]
        # Чистим старое
        while bucket and bucket[0] < window_start:
            bucket.popleft()

        limit = self._limit_for(path)
        if len(bucket) >= limit:
            retry_after = max(1, int(60 - (now - bucket[0])))
            return JSONResponse(
                {
                    "detail": f"Too many requests. Try again in {retry_after}s.",
                    "limit": limit,
                    "window": "60s",
                },
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)
        response = await call_next(request)
        # Информативные заголовки
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - len(bucket)))
        return response
