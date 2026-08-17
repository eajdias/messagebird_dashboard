from __future__ import annotations

from pydantic import BaseModel


class StatusResponse(BaseModel):
    status: str
    message: str = ""


def list_response(item_cls: type, field: str, doc: str = "") -> type:
    """Create a response model wrapping a list of items with a named field.

    Usage::
        AgentListResponse = list_response(AgentItem, "agents")
    """
    namespace = {
        "__annotations__": {field: list[item_cls]},
        field: [],
        "__doc__": doc or f"List of {item_cls.__name__}",
    }
    name = f"{item_cls.__name__}ListResponse"
    return type(name, (BaseModel,), namespace)
