from typing import List
from datetime import timedelta
from ..recon.recon_model import ExternalTxn, LedgerTxn, MatchResult
from .base_matcher import BaseMatcher
from ..config import recon_settings

class ExactMatcher(BaseMatcher):
    """Performs exact matching between external and ledger transactions"""
    
    async def match(self, 
                   external_txn: ExternalTxn, 
                   ledger_txns: List[LedgerTxn]) -> MatchResult:
        """Match using exact criteria"""
        
        # Try exact match by transaction ID in metadata
        exact_match = self._find_exact_id_match(external_txn, ledger_txns)
        if exact_match:
            return self._validate_exact_match(external_txn, exact_match)
        
        # Try exact amount + currency + timestamp match
        amount_matches = self._find_exact_amount_matches(external_txn, ledger_txns)
        if len(amount_matches) == 1:
            return self._validate_exact_match(external_txn, amount_matches[0])
        elif len(amount_matches) > 1:
            # Multiple matches - need disambiguation
            return self._create_match_result(
                external_txn,
                reason="Multiple exact amount matches found"
            )
        
        # No exact match found
        return self._create_match_result(
            external_txn,
            reason="No exact match found"
        )
    
    def _find_exact_id_match(self, 
                           external_txn: ExternalTxn, 
                           ledger_txns: List[LedgerTxn]) -> LedgerTxn:
        """Find match by exact transaction ID"""
        for ledger_txn in ledger_txns:
            # Check if external txn ID is in ledger metadata
            if 'external_txn_id' in ledger_txn.metadata:
                if ledger_txn.metadata['external_txn_id'] == external_txn.txn_id:
                    return ledger_txn
            
            # Check if ledger transaction ID is in external metadata
            if 'ledger_txn_id' in external_txn.metadata:
                if str(ledger_txn.id) == external_txn.metadata['ledger_txn_id']:
                    return ledger_txn
        
        return None
    
    def _find_exact_amount_matches(self, 
                                 external_txn: ExternalTxn, 
                                 ledger_txns: List[LedgerTxn]) -> List[LedgerTxn]:
        """Find matches by exact amount, currency, and timestamp tolerance"""
        matches = []
        tolerance = timedelta(seconds=recon_settings.timestamp_tolerance_seconds)
        
        for ledger_txn in ledger_txns:
            # Check exact amount and currency
            if (ledger_txn.amount == external_txn.amount and 
                ledger_txn.currency == external_txn.currency):
                
                # Check timestamp tolerance
                time_diff = abs(ledger_txn.timestamp - external_txn.timestamp)
                if time_diff <= tolerance:
                    matches.append(ledger_txn)
        
        return matches
    
    def _validate_exact_match(self, 
                            external_txn: ExternalTxn, 
                            ledger_txn: LedgerTxn) -> MatchResult:
        """Validate and create result for exact match"""
        
        # Check amount
        if external_txn.amount != ledger_txn.amount:
            return self._create_match_result(
                external_txn,
                ledger_txn,
                reason=f"Amount mismatch: external={external_txn.amount}, ledger={ledger_txn.amount}"
            )
        
        # Check currency
        if external_txn.currency != ledger_txn.currency:
            return self._create_match_result(
                external_txn,
                ledger_txn,
                reason=f"Currency mismatch: external={external_txn.currency}, ledger={ledger_txn.currency}"
            )
        
        # Check timestamp tolerance
        time_diff = abs(ledger_txn.timestamp - external_txn.timestamp)
        if time_diff.total_seconds() > recon_settings.timestamp_tolerance_seconds:
            return self._create_match_result(
                external_txn,
                ledger_txn,
                reason=f"Timestamp outside tolerance: diff={time_diff.total_seconds()}s"
            )
        
        # Perfect match
        return self._create_match_result(
            external_txn,
            ledger_txn,
            matched=True,
            score=1.0
        )