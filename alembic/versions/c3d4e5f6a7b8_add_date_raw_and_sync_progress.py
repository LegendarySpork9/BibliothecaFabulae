"""add date raw fields and sync progress fields

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-11-24 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("fics") as batch_op:
        batch_op.add_column(sa.Column("date_published_raw", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("date_updated_raw", sa.Text(), nullable=True))

    with op.batch_alter_table("bookmark_sync_state") as batch_op:
        batch_op.add_column(sa.Column("sync_status", sa.String(20), server_default="idle"))
        batch_op.add_column(sa.Column("sync_progress_current", sa.Integer(), server_default=sa.text("0")))
        batch_op.add_column(sa.Column("sync_progress_total", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("sync_message", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("bookmark_sync_state") as batch_op:
        batch_op.drop_column("sync_message")
        batch_op.drop_column("sync_progress_total")
        batch_op.drop_column("sync_progress_current")
        batch_op.drop_column("sync_status")

    with op.batch_alter_table("fics") as batch_op:
        batch_op.drop_column("date_updated_raw")
        batch_op.drop_column("date_published_raw")
