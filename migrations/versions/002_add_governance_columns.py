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
        with op.get_context().autocommit_block():
            op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'awaiting_approval'")
            op.execute("ALTER TYPE taskstatus ADD VALUE IF NOT EXISTS 'rejected'")

    existing = {column["name"] for column in sa.inspect(bind).get_columns("tasks")}
    columns = [
        sa.Column("requires_approval", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("approval_status", sa.String(50), server_default=sa.text("'none'")),
        sa.Column("token_cost", sa.Float(), server_default=sa.text("0.0")),
        sa.Column("trace_id", sa.String(64)),
    ]
    for column in columns:
        if column.name not in existing:
            op.add_column("tasks", column)


def downgrade() -> None:
    op.drop_column('tasks', 'trace_id')
    op.drop_column('tasks', 'token_cost')
    op.drop_column('tasks', 'approval_status')
    op.drop_column('tasks', 'requires_approval')
