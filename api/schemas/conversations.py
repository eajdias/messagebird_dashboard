from __future__ import annotations

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message_id: str = ""
    direction: str = ""
    content: str = ""
    created_at: str = ""
    agent_id: str | None = None
    agent_name: str | None = None


class ConversationItem(BaseModel):
    id: str
    contact: str = ""
    phone: str = ""
    contact_id: int = 0
    agent: str = ""
    department: str = ""
    channel: str = ""
    status: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_minutes: float | None = None
    frt_minutes: float | None = None
    art_minutes: float | None = None
    rating: float | None = None
    nps: float | None = None
    msg_count: int = 0
    reopened_count: int = 0


class ConversationListResponse(BaseModel):
    conversations: list[ConversationItem] = []
    total: int = 0
    page: int = 1
    per_page: int = 20


class ConversationDetailResponse(BaseModel):
    id: str
    contact: str = ""
    phone: str = ""
    agent: str = ""
    department: str = ""
    channel: str = ""
    status: str = ""
    start_time: str = ""
    end_time: str = ""
    duration_minutes: float | None = None
    frt_minutes: float | None = None
    art_minutes: float | None = None
    rating: float | None = None
    nps: float | None = None
    msg_count: int = 0
    reopened_count: int = 0
    messages: list[MessageResponse] = []


class ConversationMessagesResponse(BaseModel):
    conversation_id: str
    messages: list[MessageResponse] = []
    total: int = 0
