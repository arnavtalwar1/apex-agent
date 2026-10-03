"""add governance columns and approval states

Revision ID: 002_add_governance_columns
Revises: 001_initial_tables
Create Date: 2026-10-03 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002_add_governance_columns'
down_revision: Union[str, None] = '001_initial_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        try:
            op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'awaiting_approval'")
            op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'rejected'")
        except Exception:
            pass

    # Add columns safely with default fallback values
    try:
        op.add_column('tasks', sa.Column('requires_approval', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    except Exception:
        pass

    try:
        op.add_column('tasks', sa.Column('approval_status', sa.String(length=50), nullable=True, server_default=sa.text("'none'")))
    except Exception:
        pass

    try:
        op.add_column('tasks', sa.Column('token_cost', sa.Float(), nullable=True, server_default=sa.text('0.0')))
    except Exception:
        pass

    try:
        op.add_column('tasks', sa.Column('trace_id', sa.String(length=64), nullable=True))
    except Exception:
        pass


def downgrade() -> None:
    op.drop_column('tasks', 'trace_id')
    op.drop_column('tasks', 'token_cost')
    op.drop_column('tasks', 'approval_status')
    op.drop_column('tasks', 'requires_approval')
