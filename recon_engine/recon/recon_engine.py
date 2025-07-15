from datetime import date
from typing import List, Dict, Any, Optional
from uuid import UUID
import logging
from decimal import Decimal

from ..config import recon_settings
from ..ledger.ledger_reader import LedgerReader
from ..sources.csv_reader import CSVReader, BankCSVReader
from ..sources.api_adapter import APIAdapter, PaymentProcessorAdapter
from ..matchers.exact_matcher import ExactMatcher
from ..matchers.fuzzy_matcher import FuzzyMatcher
from ..recon.recon_logger import ReconLogger
from ..recon.recon_model import ExternalTxn, LedgerTxn, MatchResult, ReconStatus

logger = logging.getLogger(__name__)

class ReconEngine:
    """Main reconciliation engine orchestrator"""
    
    def __init__(self):
        self.ledger_reader = LedgerReader()
        self.recon_logger = ReconLogger()
        self.exact_matcher = ExactMatcher()
        self.fuzzy_matcher = FuzzyMatcher()
        
        # Source readers registry
        self.source_readers = {
            'csv': CSVReader(),
            'bank_csv': BankCSVReader(),
            'api': APIAdapter,  # Requires configuration
            'payment_processor': PaymentProcessorAdapter  # Requires configuration
        }
    
    async def run(self, target_date: date, source_name: str, **kwargs) -> UUID:
        """
        Run reconciliation for a specific date and source
        
        Args:
            target_date: Date to reconcile
            source_name: Source identifier (csv, bank_csv, api, etc.)
            **kwargs: Additional parameters for source readers
        
        Returns:
            UUID of the created reconciliation job
        """
        
        # Create reconciliation job
        job_id = await self.recon_logger.create_job(target_date, source_name)
        
        try:
            logger.info(f"Starting reconciliation job {job_id} for {target_date} from {source_name}")
            
            # Load external transactions
            external_txns = await self._load_external_transactions(source_name, target_date, **kwargs)
            logger.info(f"Loaded {len(external_txns)} external transactions")
            
            # Load ledger transactions
            ledger_txns = await self.ledger_reader.get_transactions_for_date(target_date)
            logger.info(f"Loaded {len(ledger_txns)} ledger transactions")
            
            # Track match statistics
            matched_count = 0
            unmatched_count = 0
            
            # Process each external transaction
            for external_txn in external_txns:
                try:
                    match_result = await self._match_transaction(external_txn, ledger_txns)
                    
                    # Enhance match result with transaction data
                    enhanced_result = self._enhance_match_result(
                        match_result, external_txn, ledger_txns
                    )
                    
                    # Log the result
                    await self.recon_logger.log_result(
                        target_date, source_name, enhanced_result
                    )
                    
                    # Update counters
                    if enhanced_result.matched:
                        matched_count += 1
                    else:
                        unmatched_count += 1
                    
                    logger.debug(f"Processed external txn {external_txn.txn_id}: "
                               f"matched={enhanced_result.matched}, score={enhanced_result.match_score:.3f}")
                
                except Exception as e:
                    logger.error(f"Error processing external transaction {external_txn.txn_id}: {str(e)}")
                    unmatched_count += 1
                    
                    # Log failed match
                    failed_result = MatchResult(
                        matched=False,
                        match_score=0.0,
                        mismatch_reason=f"Processing error: {str(e)}",
                        external_txn_id=external_txn.txn_id,
                        amount_diff=Decimal('0'),
                        timestamp_diff_seconds=0
                    )
                    
                    await self.recon_logger.log_result(
                        target_date, source_name, failed_result
                    )
            
            # Finalize job
            await self.recon_logger.finalize_job(
                job_id=job_id,
                matched_count=matched_count,
                unmatched_count=unmatched_count,
                total_external_txns=len(external_txns),
                total_ledger_txns=len(ledger_txns),
                status=ReconStatus.COMPLETED.value
            )
            
            logger.info(f"Reconciliation job {job_id} completed: "
                       f"matched={matched_count}, unmatched={unmatched_count}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Reconciliation job {job_id} failed: {str(e)}")
            
            # Mark job as failed
            await self.recon_logger.finalize_job(
                job_id=job_id,
                matched_count=0,
                unmatched_count=0,
                status=ReconStatus.FAILED.value,
                error_message=str(e)
            )
            
            raise
    
    async def _load_external_transactions(self, 
                                        source_name: str, 
                                        target_date: date, 
                                        **kwargs) -> List[ExternalTxn]:
        """Load external transactions from specified source"""
        
        if source_name in ['csv', 'bank_csv']:
            # File-based sources
            file_path = kwargs.get('file_path')
            if not file_path:
                raise ValueError(f"file_path required for {source_name} source")
            
            reader = self.source_readers[source_name]
            return reader.read_from_file(file_path)
        
        elif source_name == 'api':
            # API-based source
            base_url = kwargs.get('base_url')
            auth_token = kwargs.get('auth_token')
            
            if not base_url:
                raise ValueError("base_url required for API source")
            
            adapter = APIAdapter(base_url, auth_token)
            return await adapter.fetch_transactions(target_date)
        
        elif source_name == 'payment_processor':
            # Payment processor API
            base_url = kwargs.get('base_url')
            auth_token = kwargs.get('auth_token')
            
            if not base_url:
                raise ValueError("base_url required for payment processor source")
            
            adapter = PaymentProcessorAdapter(base_url, auth_token)
            return await adapter.fetch_settlements(target_date)
        
        else:
            raise ValueError(f"Unknown source: {source_name}")
    
    async def _match_transaction(self, 
                               external_txn: ExternalTxn, 
                               ledger_txns: List[LedgerTxn]) -> MatchResult:
        """Match a single external transaction against ledger transactions"""
        
        # Filter ledger transactions by currency for efficiency
        currency_filtered = [
            txn for txn in ledger_txns 
            if txn.currency == external_txn.currency
        ]
        
        if not currency_filtered:
            return MatchResult(
                matched=False,
                match_score=0.0,
                mismatch_reason=f"No ledger transactions found for currency {external_txn.currency}",
                external_txn_id=external_txn.txn_id,
                amount_diff=Decimal('0'),
                timestamp_diff_seconds=0
            )
        
        # Try exact matching first
        exact_result = await self.exact_matcher.match(external_txn, currency_filtered)
        
        if exact_result.matched:
            return exact_result
        
        # If no exact match, try fuzzy matching
        fuzzy_result = await self.fuzzy_matcher.match(external_txn, currency_filtered)
        
        # Return the better result
        if fuzzy_result.match_score > exact_result.match_score:
            return fuzzy_result
        else:
            return exact_result
    
    def _enhance_match_result(self, 
                            match_result: MatchResult, 
                            external_txn: ExternalTxn, 
                            ledger_txns: List[LedgerTxn]) -> MatchResult:
        """Enhance match result with additional transaction data"""
        
        # Find the matched ledger transaction
        matched_ledger_txn = None
        if match_result.ledger_txn_id:
            matched_ledger_txn = next(
                (txn for txn in ledger_txns if txn.id == match_result.ledger_txn_id),
                None
            )
        
        # Enhanced metadata
        enhanced_metadata = match_result.metadata.copy()
        enhanced_metadata.update({
            'external_amount': float(external_txn.amount),
            'external_currency': external_txn.currency,
            'external_timestamp': external_txn.timestamp.isoformat(),
            'external_description': external_txn.description
        })
        
        if matched_ledger_txn:
            enhanced_metadata.update({
                'ledger_amount': float(matched_ledger_txn.amount),
                'ledger_currency': matched_ledger_txn.currency,
                'ledger_timestamp': matched_ledger_txn.timestamp.isoformat(),
                'ledger_event_type': matched_ledger_txn.event_type
            })
        
        # Create enhanced result
        return MatchResult(
            matched=match_result.matched,
            match_score=match_result.match_score,
            mismatch_reason=match_result.mismatch_reason,
            ledger_txn_id=match_result.ledger_txn_id,
            external_txn_id=match_result.external_txn_id,
            amount_diff=match_result.amount_diff,
            timestamp_diff_seconds=match_result.timestamp_diff_seconds,
            metadata=enhanced_metadata
        )
    
    async def get_available_sources(self) -> List[str]:
        """Get list of available source readers"""
        return list(self.source_readers.keys())
    
    async def validate_source_config(self, source_name: str, **kwargs) -> bool:
        """Validate source configuration"""
        
        if source_name not in self.source_readers:
            return False
        
        if source_name in ['csv', 'bank_csv']:
            return 'file_path' in kwargs
        
        elif source_name in ['api', 'payment_processor']:
            return 'base_url' in kwargs
        
        return True