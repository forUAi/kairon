from uuid import UUID
from typing import List, Optional
from app.models.event import LedgerEvent, EventType, EventStatus
from app.database.connection import db_manager
from decimal import Decimal

class EventRepository:
    async def create_event(self, conn, event_data: dict) -> LedgerEvent:
        """Create a new ledger event"""
        query = """
            INSERT INTO ledger_events (
                source_account_id, destination_account_id, amount, currency,
                event_type, transaction_id, metadata, status
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, timestamp, source_account_id, destination_account_id,
                     amount, currency, event_type, transaction_id, metadata, status, created_at
        """
        
        row = await conn.fetchrow(
            query,
            event_data.get('source_account_id'),
            event_data.get('destination_account_id'),
            event_data['amount'],
            event_data['currency'],
            event_data['event_type'],
            event_data['transaction_id'],
            event_data.get('metadata', {}),
            event_data.get('status', 'SETTLED')
        )
        
        return LedgerEvent(**dict(row))
    
    async def get_events_by_account(self, account_id: UUID, limit: int = 100) -> List[LedgerEvent]:
        """Get events for an account"""
        query = """
            SELECT id, timestamp, source_account_id, destination_account_id,
                   amount, currency, event_type, transaction_id, metadata, status, created_at
            FROM ledger_events
            WHERE source_account_id = $1 OR destination_account_id = $1
            ORDER BY timestamp DESC
            LIMIT $2
        """
        
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch(query, account_id, limit)
            return [LedgerEvent(**dict(row)) for row in rows]
    
    async def get_events_by_transaction(self, transaction_id: UUID) -> List[LedgerEvent]:
        """Get all events for a transaction"""
        query = """
            SELECT id, timestamp, source_account_id, destination_account_id,
                   amount, currency, event_type, transaction_id, metadata, status, created_at
            FROM ledger_events
            WHERE transaction_id = $1
            ORDER BY timestamp ASC
        """
        
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch(query, transaction_id)
            return [LedgerEvent(**dict(row)) for row in rows]