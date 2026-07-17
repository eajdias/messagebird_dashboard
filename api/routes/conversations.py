"""
Conversations Routes
"""

from typing import Any

from fastapi import APIRouter, Depends, Query

from api.auth import get_current_user
from api.schemas.conversations import (
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationMessagesResponse,
)

router = APIRouter()


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
):
    """List conversations with filters and pagination."""
    # TODO: Wire to repository (fetch conversations from PG with filters)
    return ConversationListResponse(page=page, per_page=per_page)


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation(
    conversation_id: int,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get conversation detail."""
    # TODO: Wire to repository
    return ConversationDetailResponse(id=str(conversation_id))


@router.get("/{conversation_id}/messages", response_model=ConversationMessagesResponse)
async def get_conversation_messages(
    conversation_id: int,
    _current_user: dict[str, Any] = Depends(get_current_user),
):
    """Get messages for a conversation."""
    # TODO: Wire to repository
    return ConversationMessagesResponse(conversation_id=str(conversation_id))
