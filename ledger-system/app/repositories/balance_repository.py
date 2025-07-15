from uuid import UUID
from typing import Optional
from app.models.balance import Balance
from app.database.connection import db_manager
from decimal import Decimal

class BalanceRepository:
    async def get_balance(self, account_id: UUID) -> Optional[Balance]:
        """Get current balance for an account"""
        query = """
            SELECT account_id, currency, available_balance, pending_balance,
                   last_updated, version
            FROM balances
            WHERE account_id = $1
        """
        
        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, account_id)
            return Balance(**dict(row)) if row else None
    
    async def upsert_balance(self, conn, account_id: UUID, currency: str, 
                           available_delta: Decimal = Decimal('0'),
                           pending_delta: Decimal = Decimal('0')):
        """Update or insert balance atomically"""
        query = """
            INSERT INTO balances (account_id, currency, available_balance, pending_balance)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (account_id)
            DO UPDATE SET
                available_balance = balances.available_balance + $3,
                pending_balance = balances.pending_balance + $4,
                last_updated = NOW(),
                version = balances.version + 1
            RETURNING account_id, currency, available_balance, pending_balance,
                     last_updated, version
        """
        
        row = await conn.fetchrow(
            query, account_id, currency, available_delta, pending_delta
        )
        return Balance(**dict(row))
    
    async def check_sufficient_funds(self, conn, account_id: UUID, amount: Decimal) -> bool:
        """Check if account has sufficient funds"""
        query = """
            SELECT available_balance
            FROM balances
            WHERE account_id = $1
        """
        
        row = await conn.fetchrow(query, account_id)
        if not row:
            return False
        
        return row['available_balance'] >= amount