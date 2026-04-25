from pydantic import BaseModel, Field
from app.models.user import UserType, LanguageLevel


class ProfileCreate(BaseModel):
    user_type: UserType
    language_level: LanguageLevel | None = None
    experience_years: int | None = Field(None, ge=0, le=60)
    profession: str | None = Field(None, max_length=255)
    about: str | None = None
    ready_to_relocate: bool = False
    phone: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)


class ProfileUpdate(BaseModel):
    language_level: LanguageLevel | None = None
    experience_years: int | None = Field(None, ge=0, le=60)
    profession: str | None = Field(None, max_length=255)
    about: str | None = None
    ready_to_relocate: bool | None = None
    phone: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)


class ProfileResponse(BaseModel):
    id: int
    user_id: int
    user_type: UserType
    language_level: LanguageLevel | None
    experience_years: int | None
    profession: str | None
    about: str | None
    ready_to_relocate: bool
    phone: str | None
    country: str | None
    city: str | None

    model_config = {"from_attributes": True} 