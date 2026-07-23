"""Conversations Routes — wired to PostgresReportRepository."""

from __future__ import annotations

import io
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from api.auth import get_current_user
from api.dependencies import get_repository
from api.schemas.conversations import (
    ConversationDetailResponse,
    ConversationItem,
    ConversationListResponse,
    ConversationMessagesResponse,
    MessageResponse,
)
from application.interfaces.repository import ReportRepository
from domain import constants, logic

logger = logging.getLogger("api.conversations")

router = APIRouter()


def _row_to_item(r: dict[str, Any]) -> ConversationItem:
    """Convert a conversation list row dict to a ConversationItem schema."""
    agent_name = r.get("agnt_name") or "Desconhecido"
    dept_id = r.get("cnvs_dept")
    dept_label = constants.resolve_dept(dept_id) if dept_id is not None else "N/A"

    return ConversationItem(
        id=str(r["cnvs_id"]),
        contact=r.get("cnts_name") or "",
        phone=r.get("cnts_phone") or "",
        contact_id=r.get("cnts_id") or 0,
        agent=agent_name,
        department=dept_label,
        channel=constants.resolve_channel(r.get("cnvs_channel")),
        status=r.get("cnvs_status") or "",
        start_time=_fmt_dt(r.get("cnvs_created")),
        end_time=_fmt_dt(r.get("cnvs_updated")),
        rating=float(r["cnvs_rating_agent"]) if r.get("cnvs_rating_agent") is not None else None,
        nps=float(r["cnvs_rating_nps"]) if r.get("cnvs_rating_nps") is not None else None,
        msg_count=r.get("cnvs_msgcount") or 0,
        reopened_count=r.get("cnvs_reopened_count") or 0,
        art_minutes=float(r["cnvs_art_minutes"]) if r.get("cnvs_art_minutes") is not None else None,
    )


def _fmt_dt(value: Any) -> str:
    """Format datetime to local string."""
    if value is None:
        return ""
    from datetime import timedelta

    if hasattr(value, "strftime"):
        dt = value.replace(tzinfo=None) if getattr(value, "tzinfo", None) else value
        return (dt + timedelta(hours=logic.TIMEZONE_OFFSET)).strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


# ── GET /conversations/ ─────────────────────────────────────────────────


@router.get("/", response_model=ConversationListResponse)
async def list_conversations(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    department: str | None = Query(None),
    agent: str | None = Query(None),
    channel: str | None = Query(None),
    status: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """List conversations with filters and pagination."""
    rows, total = await repo.list_conversations(
        start_date=start_date,
        end_date=end_date,
        department=department,
        agent=agent,
        channel=channel,
        status=status,
        search=search,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    items = [_row_to_item(r) for r in rows]

    # Post-query filter: department is resolved from numeric ID via constants
    if department:
        items = [item for item in items if item.department == department]
        total = len(items)  # Approximate (filtered page only)

    return ConversationListResponse(
        conversations=items,
        total=total,
        page=page,
        per_page=per_page,
    )


# ── GET /conversations/{conversation_id} ────────────────────────────────


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Get conversation detail with messages."""
    detail = await repo.get_conversation_detail(conversation_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")

    agent_name = detail.get("agnt_name") or "Desconhecido"
    dept_id = detail.get("cnvs_dept")
    dept_label = constants.resolve_dept(dept_id) if dept_id is not None else "N/A"

    # Fetch messages
    raw_msgs = await repo.fetch_messages_by_conversation(conversation_id)
    messages = [
        MessageResponse(
            message_id=str(i),
            direction=m.get("msgs_direction") or "",
            content=m.get("msgs_content") or "",
            created_at=_fmt_dt(m.get("msgs_created")),
            agent_name=m.get("agnt_name"),
        )
        for i, m in enumerate(raw_msgs)
    ]

    return ConversationDetailResponse(
        id=str(detail["cnvs_id"]),
        contact=detail.get("cnts_name") or "",
        phone=detail.get("cnts_phone") or "",
        agent=agent_name,
        department=dept_label,
        channel=constants.resolve_channel(detail.get("cnvs_channel")),
        status=detail.get("cnvs_status") or "",
        start_time=_fmt_dt(detail.get("cnvs_created")),
        end_time=_fmt_dt(detail.get("cnvs_updated")),
        rating=float(detail["cnvs_rating_agent"]) if detail.get("cnvs_rating_agent") is not None else None,
        nps=float(detail["cnvs_rating_nps"]) if detail.get("cnvs_rating_nps") is not None else None,
        msg_count=detail.get("cnvs_msgcount") or 0,
        reopened_count=detail.get("cnvs_reopened_count") or 0,
        messages=messages,
    )


# ── GET /conversations/{conversation_id}/messages ───────────────────────


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: int,
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Get messages for a conversation."""
    raw_msgs = await repo.fetch_messages_by_conversation(conversation_id)
    messages = [
        MessageResponse(
            message_id=str(i),
            direction=m.get("msgs_direction") or "",
            content=m.get("msgs_content") or "",
            created_at=_fmt_dt(m.get("msgs_created")),
            agent_name=m.get("agnt_name"),
        )
        for i, m in enumerate(raw_msgs)
    ]

    return ConversationMessagesResponse(
        conversation_id=str(conversation_id),
        messages=messages,
        total=len(messages),
    )


# ── GET /conversations/{conversation_id}/pdf ──────────────────────────


@router.get("/{conversation_id}/pdf")
async def download_conversation_pdf(
    conversation_id: int,
    _current_user: dict[str, Any] = Depends(get_current_user),
    repo: ReportRepository = Depends(get_repository),
):
    """Download a PDF report for a single conversation (OS audit)."""
    detail = await repo.get_conversation_detail(conversation_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Conversation not found")

    raw_msgs = await repo.fetch_messages_by_conversation(conversation_id)

    from infrastructure.exporters.pdf_exporter import PDFExporter

    exporter = PDFExporter()
    pdf_bytes = exporter.generate_single_os_pdf_bytes(detail, raw_msgs)

    protocol = detail.get("cnvs_bird") or str(conversation_id)
    filename = f"OS_{protocol}.pdf"

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
