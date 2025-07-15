from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.models.account import Account, AccountCreate
from app.models.balance import Balance
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/account", tags=["accounts"])
ledger_service = LedgerService()

@router.post("/", response_model=Account)
async def create_account(account_data: AccountCreate):
    """Create a new account"""
    try:
        return await ledger_service.create_account(account_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{account_id}/balance", response_model=Balance)
async def get_account_balance(account_id: UUID):
    """Get account balance"""
    try:
        return await ledger_service.get_account_balance(account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))