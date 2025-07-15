from uuid import UUID
from decimal import Decimal
from typing import List
from app.models.event import LedgerEvent, EventType
from app.models.balance import Balance
from app.repositories.balance_repository import BalanceRepository

class ProjectionEngine:
    def __init__(self):
        self.balance_repo = BalanceRepository()
    
    async def project_events_to_balances(self, conn, events: List[LedgerEvent]):
        """Project events to balance updates"""
        balance_updates = {}
        
        for event in events:
            if event.event_type == EventType.DEBIT and event.source_account_id:
                # Debit decreases source account balance
                account_id = event.source_account_id
                if account_id not in balance_updates:
                    balance_updates[account_id] = {
                        'currency': event.currency,
                        'available_delta': Decimal('0'),
                        'pending_delta': Decimal('0')
                    }
                balance_updates[account_id]['available_delta'] -= event.amount
            
            elif event.event_type == EventType.CREDIT and event.destination_account_id:
                # Credit increases destination account balance
                account_id = event.destination_account_id
                if account_id not in balance_updates:
                    balance_updates[account_id] = {
                        'currency': event.currency,
                        'available_delta': Decimal('0'),
                        'pending_delta': Decimal('0')
                    }
                balance_updates[account_id]['available_delta'] += event.amount
        
        # Apply balance updates
        updated_balances = []
        for account_id, update in balance_updates.items():
            balance = await self.balance_repo.upsert_balance(
                conn, account_id, update['currency'],
                update['available_delta'], update['pending_delta']
            )
            updated_balances.append(balance)
        
        return updated_balances