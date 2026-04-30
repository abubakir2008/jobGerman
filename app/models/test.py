"""Тесты: тест → вопрос → ответ. Прохождение и результат сохраняются."""
import enum

from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class QuestionType(str, enum.Enum):
    single = "single"        # один правильный ответ
    multiple = "multiple"    # несколько правильных
    text = "text"            # короткий текстовый ответ


class Test(Base, TimestampMixin):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Та же категория что у обучающих материалов — visa/interview/relocation/work_in_germany
    category: Mapped[str | None] = mapped_column(String(50), index=True)
    # Время прохождения в минутах (0 = без ограничения)
    time_limit_min: Mapped[int] = mapped_column(Integer, default=0)
    # Минимальный процент для зачёта
    passing_score: Mapped[int] = mapped_column(Integer, default=60)
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    questions: Mapped[list["Question"]] = relationship(
        back_populates="test",
        cascade="all, delete-orphan",
        order_by="Question.position",
    )
    attempts: Mapped[list["TestAttempt"]] = relationship(
        back_populates="test", cascade="all, delete-orphan"
    )


class Question(Base, TimestampMixin):
    __tablename__ = "test_questions"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType), default=QuestionType.single, nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=1)
    # Для типа `text`: список правильных вариантов (case-insensitive, lowercase)
    correct_text_answers: Mapped[list | None] = mapped_column(JSONB, default=list)

    test: Mapped["Test"] = relationship(back_populates="questions")
    answers: Mapped[list["AnswerOption"]] = relationship(
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="AnswerOption.position",
    )


class AnswerOption(Base, TimestampMixin):
    __tablename__ = "test_answers"

    id: Mapped[int] = mapped_column(primary_key=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("test_questions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[int] = mapped_column(Integer, default=0)

    question: Mapped["Question"] = relationship(back_populates="answers")


class TestAttempt(Base, TimestampMixin):
    __tablename__ = "test_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    test_id: Mapped[int] = mapped_column(
        ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score: Mapped[int] = mapped_column(Integer, default=0)
    max_score: Mapped[int] = mapped_column(Integer, default=0)
    percentage: Mapped[float] = mapped_column(Float, default=0.0)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    # Список ответов: [{question_id, selected_answer_ids: [...], text_answer, is_correct, points}, ...]
    answers_snapshot: Mapped[list | None] = mapped_column(JSONB, default=list)

    test: Mapped["Test"] = relationship(back_populates="attempts")
