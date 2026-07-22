from api.schemas._base import list_response

# Each module is imported directly by routes via its own path.
# Re-exports kept for backward compatibility.
from api.schemas.admin import (
    AgentItem,
    AgentListResponse,
    DepartmentItem,
    DepartmentListResponse,
    HealthResponse,
    SyncProfileResponse,
    SyncStatusResponse,
    SyncTriggerRequest,
    SyncTriggerResponse,
)
from api.schemas.auth import LoginRequest, RefreshRequest, RegisterRequest, TokenResponse, UserResponse
from api.schemas.conversations import (
    ConversationDetailResponse,
    ConversationItem,
    ConversationListResponse,
    ConversationMessagesResponse,
    MessageResponse,
)
from api.schemas.dashboard import (
    AgentRankingItem,
    AgentRankingResponse,
    BSCResponse,
    ChannelItem,
    ChannelResponse,
    DashboardSummaryResponse,
    EvolutionMonth,
    EvolutionResponse,
    KPIItem,
    KPIResponse,
)
from api.schemas.reports import (
    AvailableReportItem,
    AvailableReportsResponse,
    DownloadReportResponse,
    GenerateReportResponse,
    ReportRequest,
)

__all__ = [
    "LoginRequest",
    "RegisterRequest",
    "RefreshRequest",
    "TokenResponse",
    "UserResponse",
    "DashboardSummaryResponse",
    "BSCResponse",
    "KPIItem",
    "KPIResponse",
    "EvolutionMonth",
    "EvolutionResponse",
    "AgentRankingItem",
    "AgentRankingResponse",
    "ChannelItem",
    "ChannelResponse",
    "MessageResponse",
    "ConversationItem",
    "ConversationListResponse",
    "ConversationDetailResponse",
    "ConversationMessagesResponse",
    "ReportRequest",
    "GenerateReportResponse",
    "DownloadReportResponse",
    "AvailableReportItem",
    "AvailableReportsResponse",
    "SyncProfileResponse",
    "SyncStatusResponse",
    "SyncTriggerRequest",
    "SyncTriggerResponse",
    "AgentItem",
    "AgentListResponse",
    "DepartmentItem",
    "DepartmentListResponse",
    "HealthResponse",
    "list_response",
]
