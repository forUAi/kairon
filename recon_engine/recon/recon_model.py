from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Optional, Dict, Any, List
from enum import Enum

class ReconStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class ExternalTxn(BaseModel):
    """External transaction record"""
    txn_id: str
    amount: Decimal
    currency: str
    timestamp: datetime
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}

class LedgerTxn(BaseModel):
    """Internal ledger transaction"""
    id: UUID
    transaction_id: UUID
    amount: Decimal
    currency: str
    timestamp: datetime
    event_type: str
    source_account_id: Optional[UUID] = None
    destination_account_id: Optional[UUID] = None
    metadata: Dict[str, Any] = {}

class MatchResult(BaseModel):
    """Result of matching external vs internal transaction"""
    matched: bool
    match_score: float
    mismatch_reason: Optional[str] = None
    ledger_txn_id: Optional[UUID] = None
    external_txn_id: str
    amount_diff: Decimal = Decimal('0')
    timestamp_diff_seconds: int = 0
    metadata: Dict[str, Any] = {}

class ReconLog(BaseModel):
    """Reconciliation log entry"""
    id: UUID
    recon_date: date
    source_name: str
    external_txn_id: Optional[str] = None
    ledger_txn_id: Optional[UUID] = None
    matched: bool
    mismatch_reason: Optional[str] = None
    match_score: float
    amount_difference: Decimal
    ledger_amount: Optional[Decimal] = None
    external_amount: Optional[Decimal] = None
    currency: Optional[str] = None
    timestamp_diff_seconds: Optional[int] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime

class ReconJob(BaseModel):
    """Reconciliation job tracking"""
    id: UUID
    job_date: date
    source_name: str
    status: ReconStatus
    total_external_txns: int = 0
    total_ledger_txns: int = 0
    matched_count: int = 0
    unmatched_count: int = 0
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

class ReconSummary(BaseModel):
    """Reconciliation summary"""
    job_date: date
    source_name: str
    total_external: int
    total_ledger: int
    matched: int
    unmatched: int
    match_rate: float
    amount_variance: Decimal
    major_discrepancies: List[str] = []