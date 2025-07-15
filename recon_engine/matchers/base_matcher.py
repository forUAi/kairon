from abc import ABC, abstractmethod
from typing import List, Dict, Any
from ..recon.recon_model import ExternalTxn, LedgerTxn, MatchResult

class BaseMatcher(ABC):
    """Abstract base class for transaction matchers"""
    
    @abstractmethod
    async def match(self, 
                   external_txn: ExternalTxn, 
                   ledger_txns: List[LedgerTxn]) -> MatchResult:
        """Match external transaction against ledger transactions"""
        pass
    
    def _create_match_result(self, 
                           external_txn: ExternalTxn,
                           ledger_txn: LedgerTxn = None,
                           matched: bool = False,
                           score: float = 0.0,
                           reason: str = None) -> MatchResult:
        """Create a standardized match result"""
        amount_diff = 0
        timestamp_diff = 0
        
        if ledger_txn:
            amount_diff = external_txn.amount - ledger_txn.amount
            timestamp_diff = int((external_txn.timestamp - ledger_txn.timestamp).total_seconds())
        
        return MatchResult(
            matched=matched,
            match_score=score,
            mismatch_reason=reason,
            ledger_txn_id=ledger_txn.id if ledger_txn else None,
            external_txn_id=external_txn.txn_id,
            amount_diff=amount_diff,
            timestamp_diff_seconds=timestamp_diff,
            metadata={
                'external_description': external_txn.description,
                'ledger_event_type': ledger_txn.event_type if ledger_txn else None,
                'match_criteria': self.__class__.__name__
            }
        )