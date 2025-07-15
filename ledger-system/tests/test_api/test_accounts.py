import pytest
from httpx import AsyncClient
from decimal import Decimal
from app.main import app

@pytest.mark.asyncio
class TestTransferAPI:
    
    async def test_transfer_endpoint(self, test_accounts):
        """Test transfer API endpoint"""
        alice = test_accounts["alice"]
        bob = test_accounts["bob"]
        internal_float = test_accounts["internal_float"]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Fund Alice first
            fund_response = await client.post(
                "/ledger/transfer/",
                json={
                    "source_account_id": str(internal_float.id),
                    "destination_account_id": str(alice.id),
                    "amount": "1000.00",
                    "currency": "USD",
                    "metadata": {"description": "Initial funding"}
                }
            )
            assert fund_response.status_code == 200
            
            # Transfer from Alice to Bob
            transfer_response = await client.post(
                "/ledger/transfer/",
                json={
                    "source_account_id": str(alice.id),
                    "destination_account_id": str(bob.id),
                    "amount": "150.00",
                    "currency": "USD",
                    "metadata": {"description": "Payment"}
                }
            )
            
            assert transfer_response.status_code == 200
            
            response_data = transfer_response.json()
            assert response_data["message"] == "Transfer successful"
            assert "transaction_id" in response_data
            assert response_data["events_created"] == 2
    
    async def test_transfer_validation_errors(self, test_accounts):
        """Test transfer validation errors"""
        alice = test_accounts["alice"]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Invalid amount
            response = await client.post(
                "/ledger/transfer/",
                json={
                    "source_account_id": str(alice.id),
                    "destination_account_id": str(alice.id),
                    "amount": "-100.00",
                    "currency": "USD"
                }
            )
            assert response.status_code == 422  # Validation error
            
            # Same account transfer
            response = await client.post(
                "/ledger/transfer/",
                json={
                    "source_account_id": str(alice.id),
                    "destination_account_id": str(alice.id),
                    "amount": "100.00",
                    "currency": "USD"
                }
            )
            assert response.status_code == 400