from typing import List, Dict, Any
from decimal import Decimal
from datetime import timedelta
import difflib
from ..recon.recon_model import ExternalTxn, LedgerTxn, MatchResult
from .base_matcher import BaseMatcher
from ..config import recon_settings

class FuzzyMatcher(BaseMatcher):
    """Performs fuzzy matching with configurable weights and tolerances"""
    
    async def match(self, 
                   external_txn: ExternalTxn, 
                   ledger_txns: List[LedgerTxn]) -> MatchResult:
        """Match using fuzzy logic with scoring"""
        
        best_match = None
        best_score = 0.0
        
        for ledger_txn in ledger_txns:
            score = self._calculate_match_score(external_txn, ledger_txn)
            
            if score > best_score:
                best_score = score
                best_match = ledger_txn
        
        # Check if best score meets minimum threshold
        if best_score >= recon_settings.min_match_score:
            return self._create_match_result(
                external_txn,
                best_match,
                matched=True,
                score=best_score
            )
        else:
            reason = f"Best match score {best_score:.3f} below threshold {recon_settings.min_match_score}"
            return self._create_match_result(
                external_txn,
                best_match,
                matched=False,
                score=best_score,
                reason=reason
            )
    
    def _calculate_match_score(self, 
                             external_txn: ExternalTxn, 
                             ledger_txn: LedgerTxn) -> float:
        """Calculate overall match score using weighted criteria"""
        
        # Amount similarity
        amount_score = self._calculate_amount_similarity(
            external_txn.amount, ledger_txn.amount
        )
        
        # Timestamp similarity
        timestamp_score = self._calculate_timestamp_similarity(
            external_txn.timestamp, ledger_txn.timestamp
        )
        
        # Metadata similarity
        metadata_score = self._calculate_metadata_similarity(
            external_txn, ledger_txn
        )
        
        # Currency must match exactly
        currency_score = 1.0 if external_txn.currency == ledger_txn.currency else 0.0
        
        # Weighted combination
        weights = recon_settings.fuzzy_weights
        overall_score = (
            amount_score * weights['amount'] +
            timestamp_score * weights['timestamp'] +
            metadata_score * weights['metadata']
        ) * currency_score  # Currency is a gate - must match
        
        return overall_score
    
    def _calculate_amount_similarity(self, 
                                   external_amount: Decimal, 
                                   ledger_amount: Decimal) -> float:
        """Calculate amount similarity score (0-1)"""
        if external_amount == ledger_amount:
            return 1.0
        
        # Calculate percentage difference
        avg_amount = (external_amount + ledger_amount) / 2
        if avg_amount == 0:
            return 0.0
        
        diff_percent = abs(external_amount - ledger_amount) / avg_amount
        tolerance_percent = recon_settings.amount_tolerance_percent / 100
        
        if diff_percent <= tolerance_percent:
            # Linear decay within tolerance
            return 1.0 - (diff_percent / tolerance_percent) * 0.5
        else:
            # Exponential decay outside tolerance
            return max(0.0, 0.5 * (1.0 - diff_percent))
    
    def _calculate_timestamp_similarity(self, 
                                      external_timestamp, 
                                      ledger_timestamp) -> float:
        """Calculate timestamp similarity score (0-1)"""
        time_diff = abs((external_timestamp - ledger_timestamp).total_seconds())
        tolerance = recon_settings.timestamp_tolerance_seconds
        
        if time_diff <= tolerance:
            # Linear decay within tolerance
            return 1.0 - (time_diff / tolerance) * 0.5
        else:
            # Exponential decay outside tolerance
            max_diff = tolerance * 10  # Consider up to 10x tolerance
            if time_diff > max_diff:
                return 0.0
            return 0.5 * (1.0 - (time_diff - tolerance) / (max_diff - tolerance))
    
    def _calculate_metadata_similarity(self, 
                                     external_txn: ExternalTxn, 
                                     ledger_txn: LedgerTxn) -> float:
        """Calculate metadata similarity score (0-1) using fuzzy string matching"""
        similarity_scores = []
        
        # Compare descriptions if both exist
        if external_txn.description and hasattr(ledger_txn, 'description'):
            ledger_desc = getattr(ledger_txn, 'description', '')
            if ledger_desc:
                desc_similarity = difflib.SequenceMatcher(
                    None, 
                    external_txn.description.lower().strip(),
                    ledger_desc.lower().strip()
                ).ratio()
                similarity_scores.append(desc_similarity)
        
        # Compare shared metadata fields
        external_meta = external_txn.metadata or {}
        ledger_meta = ledger_txn.metadata or {}
        
        # Find common keys
        common_keys = set(external_meta.keys()) & set(ledger_meta.keys())
        
        for key in common_keys:
            ext_value = str(external_meta[key]).lower().strip()
            ledger_value = str(ledger_meta[key]).lower().strip()
            
            # Skip empty values
            if not ext_value or not ledger_value:
                continue
            
            # Exact match gets full score
            if ext_value == ledger_value:
                similarity_scores.append(1.0)
            else:
                # Use fuzzy string matching for non-exact matches
                field_similarity = difflib.SequenceMatcher(
                    None, ext_value, ledger_value
                ).ratio()
                similarity_scores.append(field_similarity)
        
        # Special handling for transaction references
        ref_similarity = self._compare_transaction_references(external_txn, ledger_txn)
        if ref_similarity > 0:
            similarity_scores.append(ref_similarity)
        
        # Calculate weighted average of all similarity scores
        if similarity_scores:
            # Give more weight to higher similarity scores
            weighted_sum = sum(score * score for score in similarity_scores)
            weight_sum = sum(similarity_scores)
            
            if weight_sum > 0:
                return weighted_sum / weight_sum
            else:
                return 0.0
        else:
            # No comparable metadata found - neutral score
            return 0.5
    
    def _compare_transaction_references(self, 
                                      external_txn: ExternalTxn, 
                                      ledger_txn: LedgerTxn) -> float:
        """Compare transaction references and IDs for cross-linking"""
        
        # Check if external transaction ID appears in ledger metadata
        ledger_meta = ledger_txn.metadata or {}
        for key, value in ledger_meta.items():
            if 'ref' in key.lower() or 'id' in key.lower():
                if str(value).lower() == external_txn.txn_id.lower():
                    return 1.0
        
        # Check if ledger transaction ID appears in external metadata
        external_meta = external_txn.metadata or {}
        for key, value in external_meta.items():
            if 'ref' in key.lower() or 'id' in key.lower():
                if str(value).lower() == str(ledger_txn.id).lower():
                    return 1.0
        
        # Check description for ID patterns
        if external_txn.description:
            desc_lower = external_txn.description.lower()
            
            # Look for ledger transaction ID in description
            if str(ledger_txn.id).lower() in desc_lower:
                return 0.8
            
            # Look for transaction_id in description
            if str(ledger_txn.transaction_id).lower() in desc_lower:
                return 0.8
        
        return 0.0