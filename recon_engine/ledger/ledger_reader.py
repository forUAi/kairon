from datetime import date, datetime
from typing import List
from decimal import Decimal
from uuid import UUID
import asyncpg
from app.database.connection import db_manager
from ..recon.recon_model import LedgerTxn

class LedgerReader:
    """Reads internal ledger events for reconciliation"""
    
    async def get_transactions_for_date(self, target_date: date) -> List[LedgerTxn]:
        """Get all ledger transactions for a specific date"""
        query = """
            SELECT 
                id,
                transaction_id,
                amount,
                currency,
                timestamp,
                event_type,
                source_account_id,
                destination_account_id,
                metadata
            FROM ledger_events
            WHERE DATE(timestamp) = $1
            ORDER BY timestamp ASC
        """
        
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch(query, target_date)
            
            transactions = []
            for row in rows:
                transactions.append(LedgerTxn(
                    id=row['id'],
                    transaction_id=row['transaction_id'],
                    amount=Decimal(str(row['amount'])),
                    currency=row['currency'],
                    timestamp=row['timestamp'],
                    event_type=row['event_type'],
                    source_account_id=row['source_account_id'],
                    destination_account_id=row['destination_account_id'],
                    metadata=row['metadata'] or {}
                ))
            
            return transactions
    
    async def get_transaction_by_id(self, txn_id: UUID) -> LedgerTxn:
        """Get specific transaction by ID"""
        query = """
            SELECT 
                id,
                transaction_id,
                amount,
                currency,
                timestamp,
                event_type,
                source_account_id,
                destination_account_id,
                metadata
            FROM ledger_events
            WHERE id = $1
        """
        
        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, txn_id)
            
            if not row:
                raise ValueError(f"Transaction {txn_id} not found")
            
            return LedgerTxn(
                id=row['id'],
                transaction_id=row['transaction_id'],
                amount=Decimal(str(row['amount'])),
                currency=row['currency'],
                timestamp=row['timestamp'],
                event_type=row['event_type'],
                source_account_id=row['source_account_id'],
                destination_account_id=row['destination_account_id'],
                metadata=row['metadata'] or {}
            )
    
    async def get_transactions_by_amount_range(self, 
                                             target_date: date,
                                             min_amount: Decimal,
                                             max_amount: Decimal,
                                             currency: str) -> List[LedgerTxn]:
        """Get transactions within amount range for fuzzy matching"""
        query = """
            SELECT 
                id,
                transaction_id,
                amount,
                currency,
                timestamp,
                event_type,
                source_account_id,
                destination_account_id,
                metadata
            FROM ledger_events
            WHERE DATE(timestamp) = $1
            AND currency = $2
            AND amount BETWEEN $3 AND $4
            ORDER BY timestamp ASC
        """
        
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch(query, target_date, currency, min_amount, max_amount)
            
            return [LedgerTxn(
                id=row['id'],
                transaction_id=row['transaction_id'],
                amount=Decimal(str(row['amount'])),
                currency=row['currency'],
                timestamp=row['timestamp'],
                event_type=row['event_type'],
                source_account_id=row['source_account_id'],
                destination_account_id=row['destination_account_id'],
                metadata=row['metadata'] or {}
            ) for row in rows]