from uuid import UUID
from typing import Optional
from app.models.account import Account, AccountCreate
from app.database.connection import db_manager
import asyncpg

class AccountRepository:
    async def create(self, account_data: AccountCreate) -> Account:
        """Create a new account"""
        query = """
            INSERT INTO accounts (currency, type, metadata)
            VALUES ($1, $2, $3)
            RETURNING id, currency, type, metadata, created_at, updated_at
        """
        
        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow(
                query,
                account_data.currency,
                account_data.type,
                account_data.metadata
            )
            return Account(**dict(row))
    
    async def get_by_id(self, account_id: UUID) -> Optional[Account]:
        """Get account by ID"""
        query = """
            SELECT id, currency, type, metadata, created_at, updated_at
            FROM accounts
            WHERE id = $1
        """
        
        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, account_id)
            return Account(**dict(row)) if row else None
    
    async def exists(self, account_id: UUID) -> bool:
        """Check if account exists"""
        query = "SELECT 1 FROM accounts WHERE id = $1"
        
        async with db_manager.get_connection() as conn:
            result = await conn.fetchval(query, account_id)
            return result is not None