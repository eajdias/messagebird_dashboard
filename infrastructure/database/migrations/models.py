"""SQLAlchemy models for Alembic migrations.

These models mirror the PostgreSQL schema defined in 001_initial.sql.
They exist solely for migration generation — the application uses asyncpg directly.
"""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Contact(Base):
    __tablename__ = "contacts"

    cnts_id = Column(Integer, primary_key=True, autoincrement=True)
    cnts_name = Column(String(255))
    cnts_phone = Column(String(50))
    cnts_bird = Column(String(255), unique=True, nullable=False)
    cnts_created = Column(DateTime, server_default=func.current_timestamp())
    cnts_updated = Column(DateTime, server_default=func.current_timestamp())
    cnts_custom1 = Column(String(255))
    cnts_custom2 = Column(String(255))
    cnts_custom3 = Column(String(255))
    cnts_custom4 = Column(String(255))

    __table_args__ = (
        Index("idx_contacts_bird", "cnts_bird"),
        Index("idx_contacts_phone", "cnts_phone"),
    )


class Agent(Base):
    __tablename__ = "agents"

    agnt_id = Column(Integer, primary_key=True, autoincrement=True)
    agnt_name = Column(String(255))
    agnt_bird = Column(String(255), unique=True, nullable=False)
    agnt_created = Column(DateTime, server_default=func.current_timestamp())
    agnt_updated = Column(DateTime, server_default=func.current_timestamp())
    agnt_grp = Column(String(100))

    __table_args__ = (
        Index("idx_agents_bird", "agnt_bird"),
        Index("idx_agents_grp", "agnt_grp"),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    cnvs_id = Column(Integer, primary_key=True, autoincrement=True)
    cnvs_msgcount = Column(Integer, default=0)
    cnvs_cnts = Column(Integer, ForeignKey("contacts.cnts_id"))
    cnvs_agnt = Column(Integer, ForeignKey("agents.agnt_id"))
    cnvs_status = Column(String(50))
    cnvs_channel = Column(String(255))
    cnvs_bird = Column(String(255), unique=True, nullable=False)
    cnvs_created = Column(DateTime)
    cnvs_updated = Column(DateTime)
    cnvs_last = Column(DateTime)
    cnvs_lang = Column(Integer)
    cnvs_software = Column(String(255))
    cnvs_tax_id = Column(String(50))
    cnvs_dept = Column(Integer)
    cnvs_rating_agent = Column(Integer)
    cnvs_rating_nps = Column(Integer)
    cnvs_reopened_count = Column(Integer, default=0)
    cnvs_contact_reason = Column(Integer)
    cnvs_occurrence = Column(Integer)
    cnvs_description = Column(Text)

    __table_args__ = (
        Index("idx_conversations_bird", "cnvs_bird"),
        Index("idx_conversations_status", "cnvs_status"),
        Index("idx_conversations_created", "cnvs_created"),
        Index("idx_conversations_updated", "cnvs_updated"),
    )


class Message(Base):
    __tablename__ = "messages"

    msgs_id = Column(Integer, primary_key=True, autoincrement=True)
    msgs_cnvs = Column(Integer, ForeignKey("conversations.cnvs_id"), nullable=False)
    msgs_agnt = Column(Integer, ForeignKey("agents.agnt_id"))
    msgs_direction = Column(String(20))
    msgs_status = Column(String(50))
    msgs_type = Column(String(50))
    msgs_content = Column(Text)
    msgs_bird = Column(String(255), unique=True, nullable=False)
    msgs_created = Column(DateTime)
    msgs_updated = Column(DateTime)

    __table_args__ = (
        Index("idx_messages_bird", "msgs_bird"),
        Index("idx_messages_cnvs", "msgs_cnvs"),
        Index("idx_messages_created", "msgs_created"),
        Index("idx_messages_direction", "msgs_direction"),
        Index("idx_messages_cnvs_created", "msgs_cnvs", "msgs_created"),
    )


class SyncHistory(Base):
    __tablename__ = "sync"

    sync_id = Column(Integer, primary_key=True, autoincrement=True)
    sync_resource = Column(String(50), nullable=False)
    sync_created = Column(DateTime, server_default=func.current_timestamp())
    sync_duration = Column(Float)
    sync_records_count = Column(Integer)
    sync_cursor = Column(String(255))
    sync_offset = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_sync_resource_created", "sync_resource", "sync_created"),
    )


class SyncError(Base):
    __tablename__ = "sync_errors"

    err_id = Column(Integer, primary_key=True, autoincrement=True)
    err_resource = Column(String(50))
    err_code = Column(String(50))
    err_message = Column(Text)
    err_context = Column(Text)
    err_at = Column(DateTime, server_default=func.current_timestamp())
    err_retry_count = Column(Integer, default=0)
    err_resolved_at = Column(DateTime)
