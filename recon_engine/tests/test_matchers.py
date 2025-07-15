"""
Tests for financial reconciliation matchers.
Tests ExactMatcher and FuzzyMatcher components.
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel
from typing import Optional


# Mock transaction models for testing
class LedgerTxn(BaseModel):
    txn_id: str
    amount: Decimal
    timestamp: datetime
    currency: str = "USD"
    description: Optional[str] = None


class ExternalTxn(BaseModel):
    txn_id: str
    amount: Decimal
    timestamp: datetime
    currency: str = "USD"
    description: Optional[str] = None


class MatchResult(BaseModel):
    matched: bool
    match_score: float
    reason: Optional[str] = None


# Mock matcher implementations for testing
class ExactMatcher:
    """Exact matcher that requires txn_id and amount to match exactly"""
    
    async def match(self, ledger_txn: LedgerTxn, external_txn: ExternalTxn) -> MatchResult:
        """Match transactions based on exact txn_id and amount"""
        if ledger_txn.txn_id == external_txn.txn_id and ledger_txn.amount == external_txn.amount:
            return MatchResult(
                matched=True,
                match_score=1.0,
                reason="Exact match on txn_id and amount"
            )
        else:
            return MatchResult(
                matched=False,
                match_score=0.0,
                reason="txn_id or amount mismatch"
            )


class FuzzyMatcher:
    """Fuzzy matcher that uses timestamp and amount differences to score matches"""
    
    def __init__(self, time_threshold_hours: int = 1, amount_threshold: Decimal = Decimal("0.01")):
        self.time_threshold_hours = time_threshold_hours
        self.amount_threshold = amount_threshold
    
    async def match(self, ledger_txn: LedgerTxn, external_txn: ExternalTxn) -> MatchResult:
        """Match transactions based on fuzzy logic with timestamp and amount differences"""
        
        # Calculate time difference
        time_diff = abs((ledger_txn.timestamp - external_txn.timestamp).total_seconds())
        time_diff_hours = time_diff / 3600
        
        # Calculate amount difference
        amount_diff = abs(ledger_txn.amount - external_txn.amount)
        
        # Check if within thresholds
        time_within_threshold = time_diff_hours <= self.time_threshold_hours
        amount_within_threshold = amount_diff <= self.amount_threshold
        
        if time_within_threshold and amount_within_threshold:
            # Calculate match score based on how close the values are
            time_score = max(0, 1 - (time_diff_hours / self.time_threshold_hours))
            amount_score = max(0, 1 - (float(amount_diff) / float(self.amount_threshold)))
            
            # Combined score (weighted average)
            match_score = (time_score * 0.4) + (amount_score * 0.6)
            
            return MatchResult(
                matched=True,
                match_score=match_score,
                reason=f"Fuzzy match: time_diff={time_diff_hours:.2f}h, amount_diff=${amount_diff}"
            )
        else:
            return MatchResult(
                matched=False,
                match_score=0.0,
                reason=f"Outside thresholds: time_diff={time_diff_hours:.2f}h, amount_diff=${amount_diff}"
            )


# Test cases
class TestExactMatcher:
    """Test suite for ExactMatcher"""
    
    @pytest.mark.asyncio
    async def test_exact_match_returns_true_when_txn_id_and_amount_match(self):
        """Test ExactMatcher returns matched=True when txn_id and amount match exactly"""
        # Arrange
        matcher = ExactMatcher()
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        ledger_txn = LedgerTxn(
            txn_id="TXN-001",
            amount=Decimal("100.00"),
            timestamp=base_time,
            currency="USD"
        )
        
        external_txn = ExternalTxn(
            txn_id="TXN-001",
            amount=Decimal("100.00"),
            timestamp=base_time + timedelta(minutes=5),  # Different timestamp should not matter
            currency="USD"
        )
        
        # Act
        result = await matcher.match(ledger_txn, external_txn)
        
        # Assert
        assert result.matched is True
        assert result.match_score == 1.0
        assert "Exact match" in result.reason
    
    @pytest.mark.asyncio
    async def test_exact_match_returns_false_when_amount_is_different(self):
        """Test ExactMatcher returns matched=False when amount is different"""
        # Arrange
        matcher = ExactMatcher()
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        ledger_txn = LedgerTxn(
            txn_id="TXN-001",
            amount=Decimal("100.00"),
            timestamp=base_time,
            currency="USD"
        )
        
        external_txn = ExternalTxn(
            txn_id="TXN-001",  # Same txn_id
            amount=Decimal("100.50"),  # Different amount
            timestamp=base_time,
            currency="USD"
        )
        
        # Act
        result = await matcher.match(ledger_txn, external_txn)
        
        # Assert
        assert result.matched is False
        assert result.match_score == 0.0
        assert "mismatch" in result.reason


class TestFuzzyMatcher:
    """Test suite for FuzzyMatcher"""
    
    @pytest.mark.asyncio
    async def test_fuzzy_match_returns_partial_match_when_amount_close_and_timestamp_within_hour(self):
        """Test FuzzyMatcher returns partial match when amount is close and timestamp is within 1 hour"""
        # Arrange
        matcher = FuzzyMatcher(time_threshold_hours=1, amount_threshold=Decimal("0.10"))
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        ledger_txn = LedgerTxn(
            txn_id="TXN-001",
            amount=Decimal("100.00"),
            timestamp=base_time,
            currency="USD"
        )
        
        external_txn = ExternalTxn(
            txn_id="TXN-002",  # Different txn_id (doesn't matter for fuzzy matching)
            amount=Decimal("100.05"),  # Close amount (within 0.10 threshold)
            timestamp=base_time + timedelta(minutes=30),  # Within 1 hour
            currency="USD"
        )
        
        # Act
        result = await matcher.match(ledger_txn, external_txn)
        
        # Assert
        assert result.matched is True
        assert 0.0 < result.match_score <= 1.0  # Should be a partial match
        assert "Fuzzy match" in result.reason
        
        # Verify the score is reasonable (should be high since both time and amount are close)
        assert result.match_score > 0.8  # Should be high score since both are very close
    
    @pytest.mark.asyncio
    async def test_fuzzy_match_returns_false_when_outside_thresholds(self):
        """Test FuzzyMatcher returns matched=False when outside thresholds"""
        # Arrange
        matcher = FuzzyMatcher(time_threshold_hours=1, amount_threshold=Decimal("0.10"))
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        ledger_txn = LedgerTxn(
            txn_id="TXN-001",
            amount=Decimal("100.00"),
            timestamp=base_time,
            currency="USD"
        )
        
        external_txn = ExternalTxn(
            txn_id="TXN-002",
            amount=Decimal("100.00"),  # Same amount
            timestamp=base_time + timedelta(hours=2),  # Outside 1 hour threshold
            currency="USD"
        )
        
        # Act
        result = await matcher.match(ledger_txn, external_txn)
        
        # Assert
        assert result.matched is False
        assert result.match_score == 0.0
        assert "Outside thresholds" in result.reason


# Additional test to verify edge cases
class TestMatcherEdgeCases:
    """Test edge cases for matchers"""
    
    @pytest.mark.asyncio
    async def test_exact_match_with_different_txn_id_same_amount(self):
        """Test ExactMatcher fails when txn_id is different even with same amount"""
        # Arrange
        matcher = ExactMatcher()
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        ledger_txn = LedgerTxn(
            txn_id="TXN-001",
            amount=Decimal("100.00"),
            timestamp=base_time,
            currency="USD"
        )
        
        external_txn = ExternalTxn(
            txn_id="TXN-002",  # Different txn_id
            amount=Decimal("100.00"),  # Same amount
            timestamp=base_time,
            currency="USD"
        )
        
        # Act
        result = await matcher.match(ledger_txn, external_txn)
        
        # Assert
        assert result.matched is False
        assert result.match_score == 0.0
    
    @pytest.mark.asyncio
    async def test_fuzzy_match_perfect_score_with_identical_values(self):
        """Test FuzzyMatcher gives perfect score with identical timestamp and amount"""
        # Arrange
        matcher = FuzzyMatcher()
        base_time = datetime(2025, 7, 13, 10, 0, 0)
        
        ledger_txn = LedgerTxn(
            txn_id="TXN-001",
            amount=Decimal("100.00"),
            timestamp=base_time,
            currency="USD"
        )
        
        external_txn = ExternalTxn(
            txn_id="TXN-002",  # Different txn_id is fine for fuzzy matching
            amount=Decimal("100.00"),  # Identical amount
            timestamp=base_time,  # Identical timestamp
            currency="USD"
        )
        
        # Act
        result = await matcher.match(ledger_txn, external_txn)
        
        # Assert
        assert result.matched is True
        assert result.match_score == 1.0  # Perfect score
        assert "Fuzzy match" in result.reason