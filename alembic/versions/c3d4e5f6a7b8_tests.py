"""v4: tests, questions, answers, attempts

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None

questiontype_enum = postgresql.ENUM(
    'single', 'multiple', 'text', name='questiontype', create_type=False
)


def upgrade() -> None:
    # Создаём enum явно один раз — затем колонка не пытается его пересоздать.
    postgresql.ENUM(
        'single', 'multiple', 'text', name='questiontype'
    ).create(op.get_bind(), checkfirst=True)

    op.create_table(
        'tests',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True, index=True),
        sa.Column('time_limit_min', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('passing_score', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('is_published', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_table(
        'test_questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_id', sa.Integer(), sa.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('question_type', questiontype_enum, nullable=False, server_default='single'),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('points', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('correct_text_answers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        'test_answers',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('test_questions.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('position', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    op.create_table(
        'test_attempts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('test_id', sa.Integer(), sa.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('percentage', sa.Float(), nullable=False, server_default='0'),
        sa.Column('passed', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('answers_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('test_attempts')
    op.drop_table('test_answers')
    op.drop_table('test_questions')
    op.drop_table('tests')
    questiontype_enum.drop(op.get_bind(), checkfirst=True)
