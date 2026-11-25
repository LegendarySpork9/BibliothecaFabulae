"""add download job progress fields

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-11-25 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("download_jobs") as batch_op:
        batch_op.add_column(sa.Column("chapter_count", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("download_seconds", sa.Float(), nullable=True))
        batch_op.add_column(sa.Column("download_started_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("download_jobs") as batch_op:
        batch_op.drop_column("download_started_at")
        batch_op.drop_column("download_seconds")
        batch_op.drop_column("chapter_count")
