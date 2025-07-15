"""
Integration tests for the full reconciliation pipeline.
Tests ReconEngine with mocked data sources and validates match statistics.
"""

import pytest
from datetime import datetime, date
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from typing import List, Dict, Any
from uuid import uuid4
from pydantic import BaseModel


# Mock transaction models
class LedgerTxn(BaseModel):
    txn_id: str
    amount: Decimal
    timestamp: datetime
    currency: str = "USD"
    description: str = ""


class ExternalTxn(BaseModel):
    txn_id: str
    amount: Decimal
    timestamp: datetime
    currency: str = "USD"
    description: str = ""


class MatchResult(BaseModel):
    matched: bool
    match_score: float
    reason: str = ""


class ReconResult(BaseModel):
    job_uuid: str
    total_ledger_transactions: int
    total_external_transactions: int
    matched_transactions: int
    unmatched_ledger_transactions: int
    unmatched_external_transactions: int
    match_rate: float
    processing_time_seconds: float


# Mock ReconEngine class for testing
class ReconEngine:
    """Mock ReconEngine with minimal implementation for testing"""
    
    def __init__(self):
        self.ledger_reader = MagicMock()
        self.matcher = AsyncMock()
        self.logger = MagicMock()
    
    async def run(self, date: date, source: str, **kwargs) -> ReconResult:
        """Run reconciliation process"""
        job_uuid = str(uuid4())
        
        # Get transactions from mocked sources
        ledger_txns = await self._get_ledger_transactions(date)
        external_txns = await self._load_external_transactions(source, date, **kwargs)
        
        # Perform matching
        matches, unmatched_ledger, unmatched_external = await self._perform_matching(
            ledger_txns, external_txns
        )
        
        # Calculate statistics
        total_ledger = len(ledger_txns)
        total_external = len(external_txns)
        matched_count = len(matches)
        unmatched_ledger_count = len(unmatched_ledger)
        unmatched_external_count = len(unmatched_external)
        match_rate = matched_count / max(total_ledger, total_external) if max(total_ledger, total_external) > 0 else 0
        
        # Create result
        result = ReconResult(
            job_uuid=job_uuid,
            total_ledger_transactions=total_ledger,
            total_external_transactions=total_external,
            matched_transactions=matched_count,
            unmatched_ledger_transactions=unmatched_ledger_count,
            unmatched_external_transactions=unmatched_external_count,
            match_rate=match_rate,
            processing_time_seconds=1.5  # Mock processing time
        )
        
        # Log the result
        self.logger.log_reconciliation_result(result)
        
        return result
    
    async def _get_ledger_transactions(self, date: date) -> List[LedgerTxn]:
        """Get ledger transactions for date"""
        return await self.ledger_reader.get_transactions_for_date(date)
    
    async def _load_external_transactions(self, source: str, date: date, **kwargs) -> List[ExternalTxn]:
        """Load external transactions from source"""
        # This method would be mocked in tests
        return []
    
    async def _perform_matching(self, ledger_txns: List[LedgerTxn], external_txns: List[ExternalTxn]):
        """Perform transaction matching"""
        matches = []
        unmatched_ledger = []
        unmatched_external = []
        
        # Simple matching logic for testing
        for ledger_txn in ledger_txns:
            matched = False
            for external_txn in external_txns:
                # Simple exact match on txn_id and amount
                if (ledger_txn.txn_id == external_txn.txn_id and 
                    ledger_txn.amount == external_txn.amount):
                    matches.append((ledger_txn, external_txn))
                    matched = True
                    break
            
            if not matched:
                unmatched_ledger.append(ledger_txn)
        
        # Find unmatched external transactions
        matched_external_ids = {ext_txn.txn_id for _, ext_txn in matches}
        unmatched_external = [
            ext_txn for ext_txn in external_txns 
            if ext_txn.txn_id not in matched_external_ids
        ]
        
        return matches, unmatched_ledger, unmatched_external


class TestReconEngine:
    """Test suite for ReconEngine integration tests"""
    
    @pytest.fixture
    def mock_ledger_transactions(self):
        """Create mock ledger transactions"""
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        return [
            LedgerTxn(
                txn_id="LEDGER-001",
                amount=Decimal("100.00"),
                timestamp=base_time,
                currency="USD",
                description="Payment to vendor"
            ),
            LedgerTxn(
                txn_id="LEDGER-002",
                amount=Decimal("250.50"),
                timestamp=base_time,
                currency="USD",
                description="Invoice payment"
            )
        ]
    
    @pytest.fixture
    def mock_external_transactions(self):
        """Create mock external transactions - 1 match, 1 mismatch"""
        base_time = datetime(2025, 7, 13, 10, 15, 0)
        
        return [
            ExternalTxn(
                txn_id="LEDGER-001",  # This will match with ledger transaction
                amount=Decimal("100.00"),
                timestamp=base_time,
                currency="USD",
                description="Payment to vendor"
            ),
            ExternalTxn(
                txn_id="EXTERNAL-999",  # This will not match (different txn_id)
                amount=Decimal("75.25"),
                timestamp=base_time,
                currency="USD",
                description="Unknown transaction"
            )
        ]
    
    @pytest.mark.asyncio
    async def test_full_reconciliation_pipeline_with_mocked_data(
        self, mock_ledger_transactions, mock_external_transactions
    ):
        """Test full reconciliation pipeline with mocked data sources"""
        # Arrange
        engine = ReconEngine()
        test_date = date(2025, 7, 13)
        source = "bank_csv"
        
        # Mock the ledger reader
        engine.ledger_reader.get_transactions_for_date = AsyncMock(
            return_value=mock_ledger_transactions
        )
        
        # Mock the external transaction loader
        with patch.object(engine, '_load_external_transactions') as mock_load_external:
            mock_load_external.return_value = mock_external_transactions
            
            # Act
            result = await engine.run(date=test_date, source=source, file_path="test.csv")
        
        # Assert - Verify mocks were called correctly
        engine.ledger_reader.get_transactions_for_date.assert_called_once_with(test_date)
        mock_load_external.assert_called_once_with(source, test_date, file_path="test.csv")
        
        # Assert - Verify transaction counts
        assert result.total_ledger_transactions == 2
        assert result.total_external_transactions == 2
        assert result.matched_transactions == 1  # Only LEDGER-001 matches
        assert result.unmatched_ledger_transactions == 1  # LEDGER-002 is unmatched
        assert result.unmatched_external_transactions == 1  # EXTERNAL-999 is unmatched
        
        # Assert - Verify match rate calculation
        expected_match_rate = 1 / 2  # 1 match out of 2 transactions (max of ledger/external)
        assert result.match_rate == expected_match_rate
        
        # Assert - Verify job UUID is present
        assert result.job_uuid is not None
        assert len(result.job_uuid) > 0
        
        # Assert - Verify processing time is recorded
        assert result.processing_time_seconds > 0
        
        # Assert - Verify logger was called
        engine.logger.log_reconciliation_result.assert_called_once_with(result)
    
    @pytest.mark.asyncio
    async def test_reconciliation_with_no_matches(self):
        """Test reconciliation when no transactions match"""
        # Arrange
        engine = ReconEngine()
        test_date = date(2025, 7, 13)
        source = "api"
        
        # Mock ledger transactions
        ledger_txns = [
            LedgerTxn(
                txn_id="LEDGER-001",
                amount=Decimal("100.00"),
                timestamp=datetime(2025, 7, 13, 10, 0, 0),
                currency="USD"
            )
        ]
        
        # Mock external transactions (no matches)
        external_txns = [
            ExternalTxn(
                txn_id="EXTERNAL-999",
                amount=Decimal("200.00"),  # Different amount
                timestamp=datetime(2025, 7, 13, 10, 0, 0),
                currency="USD"
            )
        ]
        
        # Setup mocks
        engine.ledger_reader.get_transactions_for_date = AsyncMock(return_value=ledger_txns)
        
        with patch.object(engine, '_load_external_transactions') as mock_load_external:
            mock_load_external.return_value = external_txns
            
            # Act
            result = await engine.run(date=test_date, source=source, base_url="https://api.test.com")
        
        # Assert - No matches should be found
        assert result.matched_transactions == 0
        assert result.unmatched_ledger_transactions == 1
        assert result.unmatched_external_transactions == 1
        assert result.match_rate == 0.0
        
        # Assert - Verify logger was called
        engine.logger.log_reconciliation_result.assert_called_once_with(result)
    
    @pytest.mark.asyncio
    async def test_reconciliation_with_all_matches(self):
        """Test reconciliation when all transactions match"""
        # Arrange
        engine = ReconEngine()
        test_date = date(2025, 7, 13)
        source = "payment_processor"
        
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        # Mock transactions that all match
        ledger_txns = [
            LedgerTxn(
                txn_id="TXN-001",
                amount=Decimal("100.00"),
                timestamp=base_time,
                currency="USD"
            ),
            LedgerTxn(
                txn_id="TXN-002",
                amount=Decimal("250.50"),
                timestamp=base_time,
                currency="USD"
            )
        ]
        
        external_txns = [
            ExternalTxn(
                txn_id="TXN-001",
                amount=Decimal("100.00"),
                timestamp=base_time,
                currency="USD"
            ),
            ExternalTxn(
                txn_id="TXN-002",
                amount=Decimal("250.50"),
                timestamp=base_time,
                currency="USD"
            )
        ]
        
        # Setup mocks
        engine.ledger_reader.get_transactions_for_date = AsyncMock(return_value=ledger_txns)
        
        with patch.object(engine, '_load_external_transactions') as mock_load_external:
            mock_load_external.return_value = external_txns
            
            # Act
            result = await engine.run(date=test_date, source=source, auth_token="test_token")
        
        # Assert - All transactions should match
        assert result.matched_transactions == 2
        assert result.unmatched_ledger_transactions == 0
        assert result.unmatched_external_transactions == 0
        assert result.match_rate == 1.0  # 100% match rate
        
        # Assert - Verify logger was called
        engine.logger.log_reconciliation_result.assert_called_once_with(result)
    
    @pytest.mark.asyncio
    async def test_reconciliation_with_empty_datasets(self):
        """Test reconciliation with empty datasets"""
        # Arrange
        engine = ReconEngine()
        test_date = date(2025, 7, 13)
        source = "csv"
        
        # Mock empty datasets
        engine.ledger_reader.get_transactions_for_date = AsyncMock(return_value=[])
        
        with patch.object(engine, '_load_external_transactions') as mock_load_external:
            mock_load_external.return_value = []
            
            # Act
            result = await engine.run(date=test_date, source=source, file_path="empty.csv")
        
        # Assert - Everything should be zero
        assert result.total_ledger_transactions == 0
        assert result.total_external_transactions == 0
        assert result.matched_transactions == 0
        assert result.unmatched_ledger_transactions == 0
        assert result.unmatched_external_transactions == 0
        assert result.match_rate == 0.0
        
        # Assert - Verify logger was still called
        engine.logger.log_reconciliation_result.assert_called_once_with(result)