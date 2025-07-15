from uuid import UUID
from decimal import Decimal
from typing import Dict, Any
from app.models.event import TransferRequest
from app.repositories.account_repository import AccountRepository
from app.repositories.balance_repository import BalanceRepository
from app.config import settings

class CommandProcessor:
    def __init__(self):
        self.account_repo = AccountRepository()
        self.balance_repo = BalanceRepository()
    
    async def validate_transfer(self, transfer: TransferRequest) -> Dict[str, Any]:
        """Validate transfer command"""
        errors = []
        
        # Basic validation
        if transfer.amount <= 0:
            errors.append("Amount must be positive")
        
        if transfer.amount > settings.max_transaction_amount:
            errors.append(f"Amount exceeds maximum limit of {settings.max_transaction_amount}")
        
        if transfer.source_account_id == transfer.destination_account_id:
            errors.append("Source and destination accounts must be different")
        
        # Check if accounts exist
        source_exists = await self.account_repo.exists(transfer.source_account_id)
        if not source_exists:
            errors.append("Source account does not exist")
        
        dest_exists = await self.account_repo.exists(transfer.destination_account_id)
        if not dest_exists:
            errors.append("Destination account does not exist")
        
        # Check currency compatibility (simplified - assume same currency for now)
        if source_exists and dest_exists:
            source_account = await self.account_repo.get_by_id(transfer.source_account_id)
            dest_account = await self.account_repo.get_by_id(transfer.destination_account_id)
            
            if source_account.currency != transfer.currency:
                errors.append("Transfer currency doesn't match source account currency")
            
            if dest_account.currency != transfer.currency:
                errors.append("Transfer currency doesn't match destination account currency")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    
    async def validate_sufficient_funds(self, conn, account_id: UUID, amount: Decimal) -> bool:
        """Validate sufficient funds"""
        if settings.allow_overdraft:
            return True
        
        return await self.balance_repo.check_sufficient_funds(conn, account_id, amount)