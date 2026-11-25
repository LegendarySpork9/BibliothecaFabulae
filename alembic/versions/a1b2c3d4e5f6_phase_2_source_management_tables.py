"""phase 2 source management tables

Revision ID: a1b2c3d4e5f6
Revises: 7b75564f526b
Create Date: 2026-11-23 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7b75564f526b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_key", sa.String(50), nullable=False, unique=True),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("auth_type", sa.String(30), nullable=False, server_default="none"),
        sa.Column("auth_data_encrypted", sa.Text(), nullable=True),
        sa.Column("auth_status", sa.String(20), server_default="unknown"),
        sa.Column("auth_last_checked", sa.DateTime(), nullable=True),
        sa.Column("sync_interval_bookmarks", sa.String(50), server_default="0 2 * * *"),
        sa.Column("sync_interval_updates", sa.String(50), server_default="0 3 * * *"),
        sa.Column("rate_limit_config", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "bookmark_sync_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_site", sa.String(50), nullable=False, unique=True),
        sa.Column("last_synced", sa.DateTime(), nullable=True),
        sa.Column("last_bookmark_id", sa.String(100), nullable=True),
        sa.Column("total_bookmarks", sa.Integer(), server_default=sa.text("0")),
        sa.Column("total_synced", sa.Integer(), server_default=sa.text("0")),
    )

    op.create_table(
        "fics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_site", sa.String(50), nullable=False, index=True),
        sa.Column("source_id", sa.String(100), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("language", sa.String(50), nullable=True),
        sa.Column("rating", sa.String(50), nullable=True),
        sa.Column("warnings", sa.Text(), nullable=True),
        sa.Column("categories", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("chapter_count", sa.Integer(), nullable=True),
        sa.Column("is_complete", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("date_published", sa.DateTime(), nullable=True),
        sa.Column("date_updated", sa.DateTime(), nullable=True),
        sa.Column("date_archived", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("date_last_synced", sa.DateTime(), nullable=True),
        sa.Column("is_favourite", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("is_source_available", sa.Boolean(), server_default=sa.text("1")),
        sa.Column("reading_chapter_index", sa.Integer(), nullable=True),
        sa.Column("reading_paragraph_index", sa.Integer(), nullable=True),
        sa.Column("reading_char_offset", sa.Integer(), nullable=True),
        sa.Column("reading_status", sa.String(20), server_default="none"),
        sa.Column("html_path", sa.Text(), nullable=True),
        sa.Column("epub_path", sa.Text(), nullable=True),
        sa.Column("import_method", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.UniqueConstraint("source_site", "source_id", name="uq_fic_source"),
    )

    op.create_table(
        "chapters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fic_id", sa.Integer(), sa.ForeignKey("fics.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("chapter_number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),
        sa.Column("html_path", sa.Text(), nullable=True),
        sa.Column("word_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    op.create_table(
        "chapter_versions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("chapter_id", sa.Integer(), sa.ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("version_date", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("word_count", sa.Integer(), nullable=True),
    )

    op.create_table(
        "authors",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_site", sa.String(50), nullable=False),
        sa.Column("source_id", sa.String(100), nullable=True),
        sa.Column("profile_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "fandoms",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_site", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("tag_type", sa.String(20), nullable=False, server_default="source"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "relationships",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("relationship_type", sa.String(20), nullable=True),
        sa.Column("source_site", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "characters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_site", sa.String(50), nullable=True),
        sa.Column("gender", sa.String(20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    op.create_table(
        "fic_authors",
        sa.Column("fic_id", sa.Integer(), sa.ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("author_id", sa.Integer(), sa.ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "fic_fandoms",
        sa.Column("fic_id", sa.Integer(), sa.ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("fandom_id", sa.Integer(), sa.ForeignKey("fandoms.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "fic_tags",
        sa.Column("fic_id", sa.Integer(), sa.ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "fic_relationships",
        sa.Column("fic_id", sa.Integer(), sa.ForeignKey("fics.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("relationship_id", sa.Integer(), sa.ForeignKey("relationships.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "fic_characters",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("fic_id", sa.Integer(), sa.ForeignKey("fics.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("character_id", sa.Integer(), sa.ForeignKey("characters.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("is_pov", sa.Boolean(), server_default=sa.text("0")),
    )

    op.execute(
        "CREATE VIRTUAL TABLE IF NOT EXISTS fic_content_fts USING fts5("
        "fic_id UNINDEXED, "
        "chapter_id UNINDEXED, "
        "title, "
        "content, "
        "tokenize='porter unicode61'"
        ")"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fic_content_fts")
    op.drop_table("fic_characters")
    op.drop_table("fic_relationships")
    op.drop_table("fic_tags")
    op.drop_table("fic_fandoms")
    op.drop_table("fic_authors")
    op.drop_table("characters")
    op.drop_table("relationships")
    op.drop_table("tags")
    op.drop_table("fandoms")
    op.drop_table("authors")
    op.drop_table("chapter_versions")
    op.drop_table("chapters")
    op.drop_table("fics")
    op.drop_table("bookmark_sync_state")
    op.drop_table("sources")
