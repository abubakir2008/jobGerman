from datetime import datetime
from pydantic import BaseModel, Field

from app.models.test import QuestionType


class AnswerOptionBase(BaseModel):
    text: str
    is_correct: bool = False
    position: int = 0


class AnswerOptionResponse(AnswerOptionBase):
    id: int
    model_config = {"from_attributes": True}


# Для кандидата (без is_correct)
class AnswerOptionPublic(BaseModel):
    id: int
    text: str
    position: int = 0
    model_config = {"from_attributes": True}


class QuestionBase(BaseModel):
    text: str
    question_type: QuestionType = QuestionType.single
    position: int = 0
    points: int = Field(1, ge=1, le=100)


class QuestionUpsert(QuestionBase):
    answers: list[AnswerOptionBase] = Field(default_factory=list)
    correct_text_answers: list[str] = Field(default_factory=list)


class QuestionResponse(QuestionBase):
    id: int
    answers: list[AnswerOptionResponse] = Field(default_factory=list)
    correct_text_answers: list[str] = Field(default_factory=list)
    model_config = {"from_attributes": True}


class QuestionPublic(QuestionBase):
    """Вариант для прохождения — без правильных ответов."""
    id: int
    answers: list[AnswerOptionPublic] = Field(default_factory=list)
    model_config = {"from_attributes": True}


class TestBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    time_limit_min: int = Field(0, ge=0, le=240)
    passing_score: int = Field(60, ge=0, le=100)
    is_published: bool = True


class TestUpsert(TestBase):
    questions: list[QuestionUpsert] = Field(default_factory=list)


class TestListItem(TestBase):
    id: int
    questions_count: int = 0
    last_attempt_percentage: float | None = None
    last_attempt_passed: bool | None = None
    model_config = {"from_attributes": True}


class TestListResponse(BaseModel):
    items: list[TestListItem]
    total: int


class TestDetailResponse(TestBase):
    id: int
    questions: list[QuestionResponse] = Field(default_factory=list)
    model_config = {"from_attributes": True}


class TestPublicResponse(TestBase):
    id: int
    questions: list[QuestionPublic] = Field(default_factory=list)
    model_config = {"from_attributes": True}


# ── Прохождение ─────────────────────────────────────────────────

class AttemptAnswerInput(BaseModel):
    question_id: int
    selected_answer_ids: list[int] = Field(default_factory=list)
    text_answer: str | None = None


class AttemptSubmit(BaseModel):
    answers: list[AttemptAnswerInput] = Field(default_factory=list)


class AttemptResultEntry(BaseModel):
    question_id: int
    is_correct: bool
    points_earned: int
    selected_answer_ids: list[int] = Field(default_factory=list)
    correct_answer_ids: list[int] = Field(default_factory=list)
    text_answer: str | None = None


class AttemptResultResponse(BaseModel):
    id: int
    test_id: int
    user_id: int
    score: int
    max_score: int
    percentage: float
    passed: bool
    answers_snapshot: list[AttemptResultEntry] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class AttemptShort(BaseModel):
    id: int
    test_id: int
    test_title: str
    score: int
    max_score: int
    percentage: float
    passed: bool
    created_at: datetime
