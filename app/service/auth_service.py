from fastapi import HTTPException, status

from app.config.security import verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.schemas.auth import UserRegister, UserLogin, Token, UserResponse, RegisterResponse


class AuthService:

    def __init__(self, repo: UserRepository):
        self.repo = repo

    async def register(self, data: UserRegister) -> RegisterResponse:
        existing = await self.repo.get_by_email(data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists.",
            )
        user = await self.repo.create(data)
        token = create_access_token(subject=user.id)
        return RegisterResponse(
            user=UserResponse.model_validate(user),
            token=Token(access_token=token),
        )

    async def login(self, data: UserLogin) -> Token:
        user = await self.repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password.",
            )
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is disabled.",
            )
        token = create_access_token(subject=user.id)
        return Token(access_token=token) 