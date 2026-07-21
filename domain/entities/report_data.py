from dataclasses import dataclass, field


@dataclass
class RawMessageData:
    created: str
    direction: str
    agent_id: str | None
    agent_name: str | None


@dataclass
class RawConversationData:
    id: str
    contact: str
    phone: str
    contact_id: int = 0
    start_time: str = ""
    end_time: str = ""
    queue_time: str | None = None
    raw_created: str = ""
    raw_updated: str = ""
    msgs: list[RawMessageData] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    rating: float | None = None
    nps: float | None = None
    dept_label: str = "N/A"
    contact_reason: str = "N/A"
    occurrence: str = "N/A"


@dataclass
class ProcessedReportData:
    conversation_id: str
    agent: str
    contact_id: int = 0
    frt_min: float | None = None
    art_min: float | None = None
    duration_min: float | None = None
    rating: float | None = None
    nps: float | None = None
    dept_label: str = "N/A"
    contact_reason: str = "N/A"
    occurrence: str = "N/A"
    is_compliment: bool = False
    is_negative: bool = False
    msg_count: int = 0
    phone: str = ""
    start_time: str = ""
    end_time: str = ""
    raw_created: str = ""
