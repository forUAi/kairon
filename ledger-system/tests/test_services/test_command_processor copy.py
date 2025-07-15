import pytest
from decimal import Decimal
from uuid import uuid4
from app.models.event import TransferRequest
from app.services.ledger_service import LedgerService

@pytest.mark.asyncio
class TestLedgerService:
    
    async def test_create_account(self, ledger_service):
        """Test account creation"""
        from app.models.account import AccountCreate
        
        account_data = AccountCreate(
            currency="USD", 
            type="user", 
            metadata={"name": "Test User"}
        )
        
        account = await ledger_service.create_account(account_data)
        
        assert account.currency == "USD"
        assert account.type == "user"
        assert account.metadata["name"] == "Test User"
        
        # Check balance is initialized
        balance = await ledger_service.get_account_balance(account.id)
        assert balance.available_balance == Decimal('0')
        assert balance.pending_balance == Decimal('0')
    
    async def test_successful_transfer(self, ledger_service, test_accounts):
        """Test successful fund transfer"""
        alice = test_accounts["alice"]
        bob = test_accounts["bob"]
        internal_float = test_accounts["internal_float"]
        
        # First, fund Alice's account from internal float
        fund_request = TransferRequest(
            source_account_id=internal_float.id,
            destination_account_id=alice.id,
            amount=Decimal('1000'),
            currency="USD",
            metadata={"description": "Initial funding"}
        )
        
        fund_result = await ledger_service.transfer_funds(fund_request)
        assert fund_result["success"] is True
        
        # Check Alice's balance
        alice_balance = await ledger_service.get_account_balance(alice.id)
        assert alice_balance.available_balance == Decimal('1000')
        
        # Now transfer from Alice to Bob
        transfer_request = TransferRequest(
            source_account_id=alice.id,
            destination_account_id=bob.id,
            amount=Decimal('100'),
            currency="USD",
            metadata={"description": "Payment to Bob"}
        )
        
        result = await ledger_service.transfer_funds(transfer_request)
        assert result["success"] is True
        assert "transaction_id" in result
        
        # Check final balances
        alice_balance = await ledger_service.get_account_balance(alice.id)
        bob_balance = await ledger_service.get_account_balance(bob.id)
        
        assert alice_balance.available_balance == Decimal('900')
        assert bob_balance.available_balance == Decimal('100')
    
    async def test_insufficient_funds(self, ledger_service, test_accounts):
        """Test transfer with insufficient funds"""
        alice = test_accounts["alice"]
        bob = test_accounts["bob"]
        
        transfer_request = TransferRequest(
            source_account_id=alice.id,
            destination_account_id=bob.id,
            amount=Decimal('10000'),  # More than Alice has
            currency="USD"
        )
        
        result = await ledger_service.transfer_funds(transfer_request)
        assert result["success"] is False
        assert "Insufficient funds" in result["errors"]
    
    async def test_invalid_transfer_same_account(self, ledger_service, test_accounts):
        """Test transfer to same account"""
        alice = test_accounts["alice"]
        
        transfer_request = TransferRequest(
            source_account_id=alice.id,
            destination_account_id=alice.id,
            amount=Decimal('100'),
            currency="USD"
        )
        
        result = await ledger_service.transfer_funds(transfer_request)
        assert result["success"] is False
        assert any("same" in error.lower() for error in result["errors"])
    
    async def test_get_account_events(self, ledger_service, test_accounts):
        """Test retrieving account events"""
        alice = test_accounts["alice"]
        bob = test_accounts["bob"]
        internal_float = test_accounts["internal_float"]
        
        # Make some transactions
        transactions = [
            TransferRequest(
                source_account_id=internal_float.id,
                destination_account_id=alice.id,
                amount=Decimal('500'),
                currency="USD",
                metadata={"description": "Initial funding"}
            ),
            TransferRequest(
                source_account_id=alice.id,
                destination_account_id=bob.id,
                amount=Decimal('200'),
                currency="USD",
                metadata={"description": "Payment 1"}
            ),
            TransferRequest(
                source_account_id=alice.id,
                destination_account_id=bob.id,
                amount=Decimal('100'),
                currency="USD",
                metadata={"description": "Payment 2"}
            )
        ]
        
        for transfer in transactions:
            await ledger_service.transfer_funds(transfer)
        
        # Get Alice's events
        alice_events = await ledger_service.get_account_events(alice.id)
        
        # Alice should have 3 events: 1 credit (funding) + 2 debits (payments)
        assert len(alice_events) == 3
        
        # Check event types
        credit_events = [e for e in alice_events if e.event_type == "CREDIT"]
        debit_events = [e for e in alice_events if e.event_type == "DEBIT"]
        
        assert len(credit_events) == 1
        assert len(debit_events) == 2
        
        # Check amounts
        assert credit_events[0].amount == Decimal('500')
        assert sum(e.amount for e in debit_events) == Decimal('300')