from uuid import UUID
from typing import List, Dict, Any
from app.models.event import TransferRequest, LedgerEvent
from app.models.balance import Balance
from app.models.account import Account, AccountCreate
from app.repositories.account_repository import AccountRepository
from app.repositories.balance_repository import BalanceRepository
from app.services.command_processor import CommandProcessor
from app.services.event_store import EventStore
from app.services.projection_engine import ProjectionEngine
from app.database.connection import db_manager

class LedgerService:
    def __init__(self):
        self.account_repo = AccountRepository()
        self.balance_repo = BalanceRepository()
        self.command_processor = CommandProcessor()
        self.event_store = EventStore()
        self.projection_engine = ProjectionEngine()
    
    async def create_account(self, account_data: AccountCreate) -> Account:
        """Create a new account"""
        account = await self.account_repo.create(account_data)
        
        # Initialize balance
        async with db_manager.get_transaction() as conn:
            await self.balance_repo.upsert_balance(
                conn, account.id, account.currency
            )
        
        return account
    
    async def transfer_funds(self, transfer: TransferRequest) -> Dict[str, Any]:
        """Process a fund transfer"""
        # Validate command
        validation = await self.command_processor.validate_transfer(transfer)
        if not validation['valid']:
            return {
                'success': False,
                'errors': validation['errors']
            }
        
        # Process transfer in transaction
        async with db_manager.get_transaction() as conn:
            # Check sufficient funds
            has_funds = await self.command_processor.validate_sufficient_funds(
                conn, transfer.source_account_id, transfer.amount
            )
            if not has_funds:
                return {
                    'success': False,
                    'errors': ['Insufficient funds']
                }
            
            # Create events
            events = await self.event_store.create_transfer_events(
                conn, transfer.source_account_id, transfer.destination_account_id,
                transfer.amount, transfer.currency, transfer.metadata
            )
            
            # Project to balances
            balances = await self.projection_engine.project_events_to_balances(conn, events)
            
            return {
                'success': True,
                'transaction_id': events[0].transaction_id,
                'events': events,
                'updated_balances': balances
            }
    
    async def get_account_balance(self, account_id: UUID) -> Balance:
        """Get current account balance"""
        balance = await self.balance_repo.get_balance(account_id)
        if not balance:
            raise ValueError("Account not found or balance not initialized")
        return balance
    
    async def get_account_events(self, account_id: UUID, limit: int = 100) -> List[LedgerEvent]:
        """Get events for an account"""
        return await self.event_store.get_account_events(account_id, limit)