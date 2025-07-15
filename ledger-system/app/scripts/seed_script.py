import asyncio
from decimal import Decimal
from app.services.ledger_service import LedgerService
from app.models.account import AccountCreate
from app.models.event import TransferRequest
from app.database.connection import db_manager

async def seed_data():
    """Seed the database with test data"""
    await db_manager.connect()
    
    ledger_service = LedgerService()
    
    # Create accounts
    print("Creating accounts...")
    alice = await ledger_service.create_account(
        AccountCreate(currency="USD", type="user", metadata={"name": "Alice"})
    )
    bob = await ledger_service.create_account(
        AccountCreate(currency="USD", type="user", metadata={"name": "Bob"})
    )
    internal_float = await ledger_service.create_account(
        AccountCreate(currency="USD", type="internal", metadata={"name": "Internal Float"})
    )
    
    print(f"Alice ID: {alice.id}")
    print(f"Bob ID: {bob.id}")
    print(f"Internal Float ID: {internal_float.id}")
    
    # Seed transactions
    print("\nExecuting seed transactions...")
    
    # 1. Internal_Float tops up Alice with 500
    result1 = await ledger_service.transfer_funds(
        TransferRequest(
            source_account_id=internal_float.id,
            destination_account_id=alice.id,
            amount=Decimal('500'),
            currency="USD",
            metadata={"description": "Initial funding for Alice"}
        )
    )
    print(f"Alice funding: {result1['success']}")
    
    # 2. Alice sends 100 to Bob
    result2 = await ledger_service.transfer_funds(
        TransferRequest(
            source_account_id=alice.id,
            destination_account_id=bob.id,
            amount=Decimal('100'),
            currency="USD",
            metadata={"description": "Payment from Alice to Bob"}
        )
    )
    print(f"Alice -> Bob transfer: {result2['success']}")
    
    # 3. Bob sends 50 back to Alice
    result3 = await ledger_service.transfer_funds(
        TransferRequest(
            source_account_id=bob.id,
            destination_account_id=alice.id,
            amount=Decimal('50'),
            currency="USD",
            metadata={"description": "Refund from Bob to Alice"}
        )
    )
    print(f"Bob -> Alice transfer: {result3['success']}")
    
    # Check final balances
    print("\nFinal balances:")
    alice_balance = await ledger_service.get_account_balance(alice.id)
    bob_balance = await ledger_service.get_account_balance(bob.id)
    float_balance = await ledger_service.get_account_balance(internal_float.id)
    
    print(f"Alice: ${alice_balance.available_balance}")
    print(f"Bob: ${bob_balance.available_balance}")
    print(f"Internal Float: ${float_balance.available_balance}")
    
    await db_manager.disconnect()

if __name__ == "__main__":
    asyncio.run(seed_data())