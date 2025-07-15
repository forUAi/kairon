from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any
from enum import Enum

class EventType(str, Enum):
    DEBIT = "DEBIT"
    CREDIT = "CREDIT"
    TRANSFER = "TRANSFER"

class EventStatus(str, Enum):
    PENDING = "PENDING"
    SETTLED = "SETTLED"
    FAILED = "FAILED"

class LedgerEvent(BaseModel):
    id: UUID
    timestamp: datetime
    source_account_id: Optional[UUID]
    destination_account_id: Optional[UUID]
    amount: Decimal
    currency: str
    event_type: EventType
    transaction_id: UUID
    metadata: Dict[str, Any]
    status: EventStatus
    created_at: datetime

class TransferRequest(BaseModel):
    source_account_id: UUID
    destination_account_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    metadata: Optional[Dict[str, Any]] = {}