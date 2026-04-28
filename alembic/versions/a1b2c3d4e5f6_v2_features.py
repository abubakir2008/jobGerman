"""v2: visa doc type, stage_deadline, case_stage_history, chat_messages, notifications

Revision ID: a1b2c3d4e5f6
Revises: 7eafcd7b2d4b
Create Date: 2025-04-27

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = 'a1b2c3d4e5f6'
down_revision = '7eafcd7b2d4b'
branch_labels = None
depends_on = None

# Ссылка на уже существующий enum — create_type=False чтобы не создавать заново
existing_stage_enum = postgresql.ENUM(
    'applied', 'interview', 'documents', 'visa', 'relocation', 'completed',
    name='relocationstage',
    create_type=False,
)


def upgrade() -> None:
    # 1. Добавить значение visa в уже существующий enum DocumentType
    op.execute("ALTER TYPE documenttype ADD VALUE IF NOT EXISTS 'visa'")

    # 2. Добавить колонку stage_deadline в relocation_cases
    op.add_column(
        'relocation_cases',
        sa.Column('stage_deadline', sa.Date(), nullable=True)
    )

    # 3. Создать таблицу case_stage_history (ссылается на существующий enum)
    op.create_table(
        'case_stage_history',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('case_id', sa.Integer(),
                  sa.ForeignKey('relocation_cases.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('stage', existing_stage_enum, nullable=False),
        sa.Column('changed_by_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('changed_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
    )
    op.create_index('ix_case_stage_history_case_id', 'case_stage_history', ['case_id'])

    # 4. Создать таблицу chat_messages
    op.create_table(
        'chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('case_id', sa.Integer(),
                  sa.ForeignKey('relocation_cases.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('sender_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_chat_messages_case_id', 'chat_messages', ['case_id'])

    # 5. Создать enum notificationtype (новый тип)
    notif_enum = postgresql.ENUM(
        'stage_change', 'document_required', 'manager_note', 'new_message',
        name='notificationtype',
    )
    notif_enum.create(op.get_bind(), checkfirst=True)

    # 6. Создать таблицу notifications
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(),
                  sa.ForeignKey('users.id', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('type', postgresql.ENUM(
            'stage_change', 'document_required', 'manager_note', 'new_message',
            name='notificationtype',
            create_type=False,
        ), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('is_read', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_notifications_user_id', 'notifications')
    op.drop_table('notifications')
    postgresql.ENUM(name='notificationtype').drop(op.get_bind(), checkfirst=True)

    op.drop_index('ix_chat_messages_case_id', 'chat_messages')
    op.drop_table('chat_messages')

    op.drop_index('ix_case_stage_history_case_id', 'case_stage_history')
    op.drop_table('case_stage_history')

    op.drop_column('relocation_cases', 'stage_deadline')
    # visa из enum убрать нельзя без пересоздания типа в PostgreSQL
