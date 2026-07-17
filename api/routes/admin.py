"""
Admin Routes
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/sync/status")
async def get_sync_status():
    """Get last sync status."""
    # TODO: Implement
    return {
        "last_sync": None,
        "status": "idle",
        "records_synced": 0,
    }


@router.post("/sync/trigger")
async def trigger_sync():
    """Trigger manual sync."""
    # TODO: Implement
    return {"status": "triggered"}


@router.get("/agents")
async def list_agents():
    """List all agents."""
    # TODO: Implement
    return {"agents": []}


@router.get("/departments")
async def list_departments():
    """List all departments."""
    # TODO: Implement
    return {"departments": []}


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "2.0.0"}
