from pydantic import BaseModel
from app.models.user import UserRole


class UserRoleUpdate(BaseModel):
    role: UserRole


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: UserRole
    is_active: bool

    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int