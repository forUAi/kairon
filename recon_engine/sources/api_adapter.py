import httpx
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
from dateutil import parser
from ..recon.recon_model import ExternalTxn

class APIAdapter:
    """Adapter for fetching external transaction data from APIs"""
    
    def __init__(self, base_url: str, auth_token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
    
    async def fetch_transactions(self, target_date: date) -> List[ExternalTxn]:
        """Fetch transactions from external API for a specific date"""
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transactions",
                params={'date': target_date.isoformat()},
                headers=headers,
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            return [self._parse_api_transaction(txn) for txn in data['transactions']]
    
    def _parse_api_transaction(self, txn_data: Dict[str, Any]) -> ExternalTxn:
        """Parse API transaction data into ExternalTxn"""
        try:
            return ExternalTxn(
                txn_id=txn_data['id'],
                amount=Decimal(str(txn_data['amount'])),
                currency=txn_data['currency'].upper(),
                timestamp=parser.parse(txn_data['timestamp']),
                description=txn_data.get('description'),
                metadata=txn_data.get('metadata', {})
            )
        except Exception as e:
            raise ValueError(f"Invalid API transaction data: {str(e)}")

class PaymentProcessorAdapter(APIAdapter):
    """Specialized adapter for payment processor APIs"""
    
    async def fetch_settlements(self, target_date: date) -> List[ExternalTxn]:
        """Fetch settlement transactions"""
        headers = {}
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/settlements",
                params={
                    'settlement_date': target_date.isoformat(),
                    'status': 'settled'
                },
                headers=headers,
                timeout=30.0
            )
            
            response.raise_for_status()
            data = response.json()
            
            return [self._parse_settlement(settlement) for settlement in data['settlements']]
    
    def _parse_settlement(self, settlement_data: Dict[str, Any]) -> ExternalTxn:
        """Parse settlement data into ExternalTxn"""
        try:
            return ExternalTxn(
                txn_id=settlement_data['settlement_id'],
                amount=Decimal(str(settlement_data['net_amount'])),
                currency=settlement_data['currency'].upper(),
                timestamp=parser.parse(settlement_data['settled_at']),
                description=f"Settlement for {settlement_data.get('transaction_count', 0)} transactions",
                metadata={
                    'settlement_type': settlement_data.get('type'),
                    'transaction_count': settlement_data.get('transaction_count'),
                    'fees': settlement_data.get('fees', 0)
                }
            )
        except Exception as e:
            raise ValueError(f"Invalid settlement data: {str(e)}")
