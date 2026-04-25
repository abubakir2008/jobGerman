from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.security import get_current_user
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse, RegisterResponse
from app.service.auth_service import AuthService

router = APIRouter()


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/register", response_model=RegisterResponse, status_code=201)
async def register(
    data: UserRegister,
    service: AuthService = Depends(get_auth_service),
):
    return await service.register(data)


@router.post("/login", response_model=Token)
async def login(
    data: UserLogin,
    service: AuthService = Depends(get_auth_service),
):
    return await service.login(data)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate(current_user) 