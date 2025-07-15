from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any

class AccountCreate(BaseModel):
    currency: str = Field(..., min_length=3, max_length=3)
    type: str = Field(..., min_length=1, max_length=50)
    metadata: Optional[Dict[str, Any]] = {}

class Account(BaseModel):
    id: UUID
    currency: str
    type: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True