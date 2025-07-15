from fastapi import APIRouter, HTTPException, Query
from uuid import UUID
from typing import List
from app.models.event import LedgerEvent
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/events", tags=["events"])
ledger_service = LedgerService()

@router.get("/", response_model=List[LedgerEvent])
async def get_events(
    account_id: UUID = Query(..., description="Account ID to get events for"),
    limit: int = Query(100, ge=1, le=1000, description="Number of events to return")
):
    """Get events for an account"""
    try:
        return await ledger_service.get_account_events(account_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))