"""initial schema

Create initial PostgreSQL schema mirroring the legacy SQLite database
with column renames preserved for backward compatibility.

Revision ID: 001
Revises: None
Create Date: 2026-07-17

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "contacts",
        sa.Column("cnts_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnts_name", sa.String(255), nullable=True),
        sa.Column("cnts_phone", sa.String(50), nullable=True),
        sa.Column("cnts_bird", sa.String(255), nullable=False),
        sa.Column("cnts_created", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("cnts_updated", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("cnts_custom1", sa.String(255), nullable=True),
        sa.Column("cnts_custom2", sa.String(255), nullable=True),
        sa.Column("cnts_custom3", sa.String(255), nullable=True),
        sa.Column("cnts_custom4", sa.String(255), nullable=True),
        sa.PrimaryKeyConstraint("cnts_id"),
        sa.UniqueConstraint("cnts_bird"),
    )
    op.create_index("idx_contacts_bird", "contacts", ["cnts_bird"])
    op.create_index("idx_contacts_phone", "contacts", ["cnts_phone"])

    op.create_table(
        "agents",
        sa.Column("agnt_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("agnt_name", sa.String(255), nullable=True),
        sa.Column("agnt_bird", sa.String(255), nullable=False),
        sa.Column("agnt_created", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("agnt_updated", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("agnt_grp", sa.String(100), nullable=True),
        sa.PrimaryKeyConstraint("agnt_id"),
        sa.UniqueConstraint("agnt_bird"),
    )
    op.create_index("idx_agents_bird", "agents", ["agnt_bird"])
    op.create_index("idx_agents_grp", "agents", ["agnt_grp"])

    op.create_table(
        "conversations",
        sa.Column("cnvs_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cnvs_msgcount", sa.Integer(), server_default="0", nullable=True),
        sa.Column("cnvs_cnts", sa.Integer(), sa.ForeignKey("contacts.cnts_id"), nullable=True),
        sa.Column("cnvs_agnt", sa.Integer(), sa.ForeignKey("agents.agnt_id"), nullable=True),
        sa.Column("cnvs_status", sa.String(50), nullable=True),
        sa.Column("cnvs_channel", sa.String(255), nullable=True),
        sa.Column("cnvs_bird", sa.String(255), nullable=False),
        sa.Column("cnvs_created", sa.DateTime(), nullable=True),
        sa.Column("cnvs_updated", sa.DateTime(), nullable=True),
        sa.Column("cnvs_last", sa.DateTime(), nullable=True),
        sa.Column("cnvs_lang", sa.Integer(), nullable=True),
        sa.Column("cnvs_software", sa.String(255), nullable=True),
        sa.Column("cnvs_tax_id", sa.String(50), nullable=True),
        sa.Column("cnvs_dept", sa.Integer(), nullable=True),
        sa.Column("cnvs_rating_agent", sa.Integer(), nullable=True),
        sa.Column("cnvs_rating_nps", sa.Integer(), nullable=True),
        sa.Column("cnvs_reopened_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("cnvs_contact_reason", sa.Integer(), nullable=True),
        sa.Column("cnvs_occurrence", sa.Integer(), nullable=True),
        sa.Column("cnvs_description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("cnvs_id"),
        sa.UniqueConstraint("cnvs_bird"),
    )
    op.create_index("idx_conversations_bird", "conversations", ["cnvs_bird"])
    op.create_index("idx_conversations_status", "conversations", ["cnvs_status"])
    op.create_index("idx_conversations_created", "conversations", ["cnvs_created"])
    op.create_index("idx_conversations_updated", "conversations", ["cnvs_updated"])

    op.create_table(
        "messages",
        sa.Column("msgs_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("msgs_cnvs", sa.Integer(), sa.ForeignKey("conversations.cnvs_id"), nullable=False),
        sa.Column("msgs_agnt", sa.Integer(), sa.ForeignKey("agents.agnt_id"), nullable=True),
        sa.Column("msgs_direction", sa.String(20), nullable=True),
        sa.Column("msgs_status", sa.String(50), nullable=True),
        sa.Column("msgs_type", sa.String(50), nullable=True),
        sa.Column("msgs_content", sa.Text(), nullable=True),
        sa.Column("msgs_bird", sa.String(255), nullable=False),
        sa.Column("msgs_created", sa.DateTime(), nullable=True),
        sa.Column("msgs_updated", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("msgs_id"),
        sa.UniqueConstraint("msgs_bird"),
    )
    op.create_index("idx_messages_bird", "messages", ["msgs_bird"])
    op.create_index("idx_messages_cnvs", "messages", ["msgs_cnvs"])
    op.create_index("idx_messages_created", "messages", ["msgs_created"])
    op.create_index("idx_messages_direction", "messages", ["msgs_direction"])
    op.create_index("idx_messages_cnvs_created", "messages", ["msgs_cnvs", "msgs_created"])

    op.create_table(
        "sync",
        sa.Column("sync_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("sync_resource", sa.String(50), nullable=False),
        sa.Column("sync_created", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("sync_duration", sa.Float(), nullable=True),
        sa.Column("sync_records_count", sa.Integer(), nullable=True),
        sa.Column("sync_cursor", sa.String(255), nullable=True),
        sa.Column("sync_offset", sa.Integer(), server_default="0", nullable=True),
        sa.PrimaryKeyConstraint("sync_id"),
    )
    op.create_index("idx_sync_resource_created", "sync", ["sync_resource", "sync_created"])

    op.create_table(
        "sync_errors",
        sa.Column("err_id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("err_resource", sa.String(50), nullable=True),
        sa.Column("err_code", sa.String(50), nullable=True),
        sa.Column("err_message", sa.Text(), nullable=True),
        sa.Column("err_context", sa.Text(), nullable=True),
        sa.Column("err_at", sa.DateTime(), server_default=sa.func.current_timestamp(), nullable=True),
        sa.Column("err_retry_count", sa.Integer(), server_default="0", nullable=True),
        sa.Column("err_resolved_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("err_id"),
    )


def downgrade() -> None:
    op.drop_table("sync_errors")
    op.drop_table("sync")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("agents")
    op.drop_table("contacts")
