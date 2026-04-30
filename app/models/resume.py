from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Resume(Base, TimestampMixin):
    """Структурированное резюме кандидата (1:1 с пользователем).

    Сложные многозначные секции хранятся как JSONB-массивы — это позволяет
    добавлять/убирать поля без миграций и легко рендерится на фронте.
    """
    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )

    # ── Контакты / профиль ────────────────────────────────────
    full_name: Mapped[str | None] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50))
    email: Mapped[str | None] = mapped_column(String(255))
    city: Mapped[str | None] = mapped_column(String(100))
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    github_url: Mapped[str | None] = mapped_column(String(500))

    # ── Цель / о себе ─────────────────────────────────────────
    desired_position: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)

    # ── Многозначные секции (JSON) ────────────────────────────
    # skills: ["Python", "FastAPI", ...]
    skills: Mapped[list | None] = mapped_column(JSONB, default=list)
    # experience: [{title, company, period, description}, ...]
    experience: Mapped[list | None] = mapped_column(JSONB, default=list)
    # projects: [{name, link, description}, ...]
    projects: Mapped[list | None] = mapped_column(JSONB, default=list)
    # education: [{institution, degree, period}, ...]
    education: Mapped[list | None] = mapped_column(JSONB, default=list)
    # languages: [{name, level}, ...]
    languages: Mapped[list | None] = mapped_column(JSONB, default=list)
    # extras: [{title, description}, ...] — курсы/сертификаты/достижения
    extras: Mapped[list | None] = mapped_column(JSONB, default=list)

    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<Resume user_id={self.user_id}>"
