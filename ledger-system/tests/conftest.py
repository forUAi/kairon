import pytest
import asyncio
from uuid import uuid4
from decimal import Decimal
from app.models.account import AccountCreate
from app.services.ledger_service import LedgerService
from app.database.connection import db_manager

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def setup_database():
    await db_manager.connect()
    yield
    await db_manager.disconnect()

@pytest.fixture
async def ledger_service():
    return LedgerService()

@pytest.fixture
async def test_accounts(ledger_service):
    """Create test accounts"""
    alice = await ledger_service.create_account(
        AccountCreate(currency="USD", type="user", metadata={"name": "Alice"})
    )
    bob = await ledger_service.create_account(
        AccountCreate(currency="USD", type="user", metadata={"name": "Bob"})
    )
    internal_float = await ledger_service.create_account(
        AccountCreate(currency="USD", type="internal", metadata={"name": "Internal Float"})
    )
    
    return {
        "alice": alice,
        "bob": bob,
        "internal_float": internal_float
    }