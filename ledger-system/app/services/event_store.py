from uuid import UUID, uuid4
from decimal import Decimal
from typing import List, Dict, Any
from app.models.event import LedgerEvent, EventType, EventStatus
from app.repositories.event_repository import EventRepository

class EventStore:
    def __init__(self):
        self.event_repo = EventRepository()
    
    async def create_transfer_events(self, conn, source_account_id: UUID, 
                                   destination_account_id: UUID, amount: Decimal,
                                   currency: str, metadata: Dict[str, Any]) -> List[LedgerEvent]:
        """Create double-entry events for a transfer"""
        transaction_id = uuid4()
        
        # Create debit event (money leaving source account)
        debit_event = await self.event_repo.create_event(conn, {
            'source_account_id': source_account_id,
            'destination_account_id': None,
            'amount': amount,
            'currency': currency,
            'event_type': EventType.DEBIT,
            'transaction_id': transaction_id,
            'metadata': metadata,
            'status': EventStatus.SETTLED
        })
        
        # Create credit event (money entering destination account)
        credit_event = await self.event_repo.create_event(conn, {
            'source_account_id': None,
            'destination_account_id': destination_account_id,
            'amount': amount,
            'currency': currency,
            'event_type': EventType.CREDIT,
            'transaction_id': transaction_id,
            'metadata': metadata,
            'status': EventStatus.SETTLED
        })
        
        return [debit_event, credit_event]
    
    async def get_account_events(self, account_id: UUID, limit: int = 100) -> List[LedgerEvent]:
        """Get events for an account"""
        return await self.event_repo.get_events_by_account(account_id, limit)
    
    async def get_transaction_events(self, transaction_id: UUID) -> List[LedgerEvent]:
        """Get all events for a transaction"""
        return await self.event_repo.get_events_by_transaction(transaction_id)