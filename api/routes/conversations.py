"""
Conversations Routes
"""


from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/")
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
):
    """List conversations with filters and pagination."""
    # TODO: Implement
    return {
        "conversations": [],
        "total": 0,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Get conversation detail."""
    # TODO: Implement
    return {"id": conversation_id, "messages": []}


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int):
    """Get messages for a conversation."""
    # TODO: Implement
    return {"messages": []}
