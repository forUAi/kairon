from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from decimal import Decimal

class Balance(BaseModel):
    account_id: UUID
    currency: str
    available_balance: Decimal
    pending_balance: Decimal
    last_updated: datetime
    version: int

    class Config:
        from_attributes = True
