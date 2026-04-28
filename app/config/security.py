from datetime import datetime, timedelta, timezone
# импорт необходимых библиотек для безопасности и работы с JWT, а также для хэширования паролей
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
# импорт настроек и функции получения базы данных
from app.config.config import settings
from app.config.database import get_db

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",
)


bearer_scheme = HTTPBearer()

# нельзя трагать методы ниже, иначе сломается безопасность, если нужно что-то изменить, то только в рамках этих методов, а не их логики
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str | int, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


def decode_token(token: str) -> int | None:
    """Декодирует JWT и возвращает user_id как int (для WebSocket)."""
    sub = decode_access_token(token)
    try:
        return int(sub) if sub else None
    except (ValueError, TypeError):
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    from app.repositories.user_repository import UserRepository

    token = credentials.credentials
    user_id = decode_access_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
        )

    user = await UserRepository(db).get_by_id(int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive.",
        )
    return user


async def require_admin(current_user=Depends(get_current_user)):
    from app.models.user import UserRole
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return current_user


async def require_manager(current_user=Depends(get_current_user)):
    from app.models.user import UserRole
    if current_user.role not in (UserRole.manager, UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager access required.",
        )
    return current_user