
import enum
 
from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
 
from app.models import Base, TimestampMixin
 
 
class UserRole(enum.Enum):
    candidate = "candidate"
    manager = "manager"
    admin = "admin"


class UserType(str , enum.Enum):
    student = "student"
    worker = "worker"

class languageLevel(str, enum.Enum):
    a1 = "A1"
    a2 = "A2"
    b1 = "B1"
    b2 = "B2"
    c1 = "C1"
    c2 = "C2"


class User(Base, TimestampMixin):
    __tablename__ = "users"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.candidate)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
 
    profile: Mapped["CandidateProfile"] = relationship(back_populates="user", uselist=False)
    applications: Mapped[list["Application"]] = relationship(back_populates="candidate")  # noqa: F821
    managed_cases: Mapped[list["RelocationCase"]] = relationship(back_populates="manager")  # noqa: F821
 
 
    def __repr__(self) -> str:
        return f"<User {self.email}>"
 


class CandidateProfile(Base, TimestampMixin):
    __tablename__ = "candidate_profiles"
 
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    user_type: Mapped[UserType] = mapped_column(Enum(UserType), nullable=False)
    language_level: Mapped[LanguageLevel | None] = mapped_column(Enum(LanguageLevel))
    experience_years: Mapped[int | None] = mapped_column(default=0)
    profession: Mapped[str | None] = mapped_column(String(255))
    about: Mapped[str | None] = mapped_column(Text)
    ready_to_relocate: Mapped[bool] = mapped_column(Boolean, default=False)
    phone: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(100))
    city: Mapped[str | None] = mapped_column(String(100))
 
    # Relationships
    user: Mapped["User"] = relationship(back_populates="profile")
    documents: Mapped[list["Document"]] = relationship(back_populates="candidate")  # noqa: F821
 
    def __repr__(self) -> str:
        return f"<CandidateProfile user_id={self.user_id}>"
 
 