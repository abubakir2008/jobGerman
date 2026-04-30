"""v3: resumes table + applications.cv_document_id

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Таблица резюме
    op.create_table(
        'resumes',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column(
            'user_id',
            sa.Integer(),
            sa.ForeignKey('users.id', ondelete='CASCADE'),
            nullable=False,
            unique=True,
        ),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('desired_position', sa.String(length=255), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('skills', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('experience', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('projects', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('education', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('languages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('extras', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )
    op.create_index('ix_resumes_user_id', 'resumes', ['user_id'])

    # cv_document_id в applications
    op.add_column(
        'applications',
        sa.Column('cv_document_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_applications_cv_document_id',
        'applications',
        'documents',
        ['cv_document_id'],
        ['id'],
        ondelete='SET NULL',
    )


def downgrade() -> None:
    op.drop_constraint('fk_applications_cv_document_id', 'applications', type_='foreignkey')
    op.drop_column('applications', 'cv_document_id')
    op.drop_index('ix_resumes_user_id', table_name='resumes')
    op.drop_table('resumes')
