from pydantic import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost/ledger_db"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    
    # Business rules
    allow_overdraft: bool = False
    max_transaction_amount: float = 1000000.0
    
    class Config:
        env_file = ".env"

settings = Settings()