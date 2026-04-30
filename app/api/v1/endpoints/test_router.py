"""Тесты: список, прохождение, конструктор для админа, результаты."""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config.database import get_db
from app.config.security import get_current_user, require_admin
from app.models.test import (
    AnswerOption,
    Question,
    QuestionType,
    Test,
    TestAttempt,
)
from app.models.user import User
from app.schemas.test import (
    AttemptResultEntry,
    AttemptResultResponse,
    AttemptShort,
    AttemptSubmit,
    QuestionResponse,
    TestDetailResponse,
    TestListItem,
    TestListResponse,
    TestPublicResponse,
    TestUpsert,
)

router = APIRouter()


# ── PUBLIC: список тестов и прохождение ──────────────────────────

@router.get("", response_model=TestListResponse)
async def list_tests(
    category: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Test).where(Test.is_published.is_(True))
    if category:
        query = query.where(Test.category == category)
    query = query.order_by(desc(Test.created_at))

    result = await db.execute(query)
    tests = result.scalars().all()

    # Кол-во вопросов
    counts: dict[int, int] = {}
    if tests:
        cnt_rows = await db.execute(
            select(Question.test_id, func.count(Question.id))
            .where(Question.test_id.in_([t.id for t in tests]))
            .group_by(Question.test_id)
        )
        counts = {tid: c for tid, c in cnt_rows.all()}

    # Последняя попытка пользователя
    last_attempts: dict[int, TestAttempt] = {}
    if tests:
        rows = await db.execute(
            select(TestAttempt)
            .where(
                TestAttempt.user_id == current_user.id,
                TestAttempt.test_id.in_([t.id for t in tests]),
            )
            .order_by(desc(TestAttempt.created_at))
        )
        for a in rows.scalars().all():
            last_attempts.setdefault(a.test_id, a)

    items = [
        TestListItem(
            id=t.id,
            title=t.title,
            description=t.description,
            category=t.category,
            time_limit_min=t.time_limit_min,
            passing_score=t.passing_score,
            is_published=t.is_published,
            questions_count=counts.get(t.id, 0),
            last_attempt_percentage=last_attempts[t.id].percentage if t.id in last_attempts else None,
            last_attempt_passed=last_attempts[t.id].passed if t.id in last_attempts else None,
        )
        for t in tests
    ]
    return TestListResponse(items=items, total=len(items))


async def _load_test_with_questions(db: AsyncSession, test_id: int) -> Test | None:
    result = await db.execute(
        select(Test)
        .where(Test.id == test_id)
        .options(selectinload(Test.questions).selectinload(Question.answers))
    )
    return result.scalar_one_or_none()


@router.get("/{test_id}", response_model=TestPublicResponse)
async def get_test_for_taking(
    test_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Получить тест без правильных ответов — для прохождения."""
    test = await _load_test_with_questions(db, test_id)
    if not test or not test.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found.")
    return test


@router.post("/{test_id}/submit", response_model=AttemptResultResponse, status_code=201)
async def submit_test(
    test_id: int,
    payload: AttemptSubmit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Принять ответы, посчитать баллы, сохранить попытку."""
    test = await _load_test_with_questions(db, test_id)
    if not test or not test.is_published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found.")

    # Маппинг question_id → Question, чтобы быстро искать
    qmap: dict[int, Question] = {q.id: q for q in test.questions}
    answer_inputs = {a.question_id: a for a in payload.answers}

    score = 0
    max_score = 0
    snapshot: list[dict] = []

    for q in test.questions:
        max_score += q.points
        ai = answer_inputs.get(q.id)
        selected_ids = ai.selected_answer_ids if ai else []
        text_answer = ai.text_answer if ai else None

        correct_ids = sorted(a.id for a in q.answers if a.is_correct)
        is_correct = False

        if q.question_type == QuestionType.single:
            # ровно один правильный ответ должен совпасть
            is_correct = (
                len(selected_ids) == 1
                and selected_ids[0] in correct_ids
            )
        elif q.question_type == QuestionType.multiple:
            is_correct = sorted(selected_ids) == correct_ids and len(correct_ids) > 0
        elif q.question_type == QuestionType.text:
            normalized = (text_answer or "").strip().lower()
            corrects = [c.strip().lower() for c in (q.correct_text_answers or [])]
            is_correct = bool(normalized) and normalized in corrects

        if is_correct:
            score += q.points

        snapshot.append({
            "question_id": q.id,
            "is_correct": is_correct,
            "points_earned": q.points if is_correct else 0,
            "selected_answer_ids": selected_ids,
            "correct_answer_ids": correct_ids,
            "text_answer": text_answer,
        })

    percentage = round((score / max_score) * 100, 2) if max_score > 0 else 0.0
    passed = percentage >= test.passing_score

    attempt = TestAttempt(
        test_id=test.id,
        user_id=current_user.id,
        score=score,
        max_score=max_score,
        percentage=percentage,
        passed=passed,
        answers_snapshot=snapshot,
    )
    db.add(attempt)
    await db.commit()
    await db.refresh(attempt)
    return attempt


@router.get("/attempts/me", response_model=list[AttemptShort])
async def my_attempts(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = await db.execute(
        select(TestAttempt, Test.title)
        .join(Test, Test.id == TestAttempt.test_id)
        .where(TestAttempt.user_id == current_user.id)
        .order_by(desc(TestAttempt.created_at))
    )
    out: list[AttemptShort] = []
    for attempt, title in rows.all():
        out.append(
            AttemptShort(
                id=attempt.id,
                test_id=attempt.test_id,
                test_title=title,
                score=attempt.score,
                max_score=attempt.max_score,
                percentage=attempt.percentage,
                passed=attempt.passed,
                created_at=attempt.created_at,
            )
        )
    return out


# ── ADMIN: CRUD тестов ──────────────────────────────────────────

@router.get("/admin/all", response_model=TestListResponse)
async def admin_list_tests(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Список ВСЕХ тестов — для админа (включая черновики)."""
    rows = await db.execute(select(Test).order_by(desc(Test.created_at)))
    tests = rows.scalars().all()

    counts: dict[int, int] = {}
    if tests:
        cnt_rows = await db.execute(
            select(Question.test_id, func.count(Question.id))
            .where(Question.test_id.in_([t.id for t in tests]))
            .group_by(Question.test_id)
        )
        counts = {tid: c for tid, c in cnt_rows.all()}

    items = [
        TestListItem(
            id=t.id,
            title=t.title,
            description=t.description,
            category=t.category,
            time_limit_min=t.time_limit_min,
            passing_score=t.passing_score,
            is_published=t.is_published,
            questions_count=counts.get(t.id, 0),
        )
        for t in tests
    ]
    return TestListResponse(items=items, total=len(items))


@router.get("/admin/{test_id}", response_model=TestDetailResponse)
async def admin_get_test(
    test_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Тест с правильными ответами — только админу."""
    test = await _load_test_with_questions(db, test_id)
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found.")
    return test


@router.post("/admin", response_model=TestDetailResponse, status_code=201)
async def admin_create_test(
    payload: TestUpsert,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    test = Test(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        time_limit_min=payload.time_limit_min,
        passing_score=payload.passing_score,
        is_published=payload.is_published,
        created_by_id=current_user.id,
    )
    for qi, qd in enumerate(payload.questions):
        q = Question(
            text=qd.text,
            question_type=qd.question_type,
            position=qd.position or qi,
            points=qd.points,
            correct_text_answers=qd.correct_text_answers or [],
        )
        for ai, ad in enumerate(qd.answers):
            q.answers.append(
                AnswerOption(
                    text=ad.text,
                    is_correct=ad.is_correct,
                    position=ad.position or ai,
                )
            )
        test.questions.append(q)
    db.add(test)
    await db.commit()
    return await _load_test_with_questions(db, test.id)


@router.put("/admin/{test_id}", response_model=TestDetailResponse)
async def admin_update_test(
    test_id: int,
    payload: TestUpsert,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    test = await _load_test_with_questions(db, test_id)
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found.")

    test.title = payload.title
    test.description = payload.description
    test.category = payload.category
    test.time_limit_min = payload.time_limit_min
    test.passing_score = payload.passing_score
    test.is_published = payload.is_published

    # Простейший подход: удалить старые вопросы, создать новые.
    for q in list(test.questions):
        await db.delete(q)
    await db.flush()

    for qi, qd in enumerate(payload.questions):
        q = Question(
            test_id=test.id,
            text=qd.text,
            question_type=qd.question_type,
            position=qd.position or qi,
            points=qd.points,
            correct_text_answers=qd.correct_text_answers or [],
        )
        for ai, ad in enumerate(qd.answers):
            q.answers.append(
                AnswerOption(
                    text=ad.text,
                    is_correct=ad.is_correct,
                    position=ad.position or ai,
                )
            )
        db.add(q)

    await db.commit()
    return await _load_test_with_questions(db, test.id)


@router.delete("/admin/{test_id}", status_code=204)
async def admin_delete_test(
    test_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    test = await db.scalar(select(Test).where(Test.id == test_id))
    if not test:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Test not found.")
    await db.delete(test)
    await db.commit()
