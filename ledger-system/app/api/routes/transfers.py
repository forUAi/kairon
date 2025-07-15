from fastapi import APIRouter, HTTPException
from app.models.event import TransferRequest
from app.services.ledger_service import LedgerService

router = APIRouter(prefix="/transfer", tags=["transfers"])
ledger_service = LedgerService()

@router.post("/")
async def transfer_funds(transfer: TransferRequest):
    """Transfer funds between accounts"""
    try:
        result = await ledger_service.transfer_funds(transfer)
        
        if not result['success']:
            raise HTTPException(status_code=400, detail={
                'message': 'Transfer failed',
                'errors': result['errors']
            })
        
        return {
            'message': 'Transfer successful',
            'transaction_id': result['transaction_id'],
            'events_created': len(result['events'])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))