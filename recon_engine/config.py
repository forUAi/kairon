from pydantic import BaseSettings
from typing import Dict, Any

class ReconSettings(BaseSettings):
    # Database connection (inherit from main app)
    database_url: str = "postgresql://user:password@localhost/ledger_db"
    
    # Matching tolerances
    amount_tolerance_percent: float = 0.1  # 0.1% tolerance
    timestamp_tolerance_seconds: int = 300  # 5 minutes
    
    # Fuzzy matching weights
    fuzzy_weights: Dict[str, float] = {
        "amount": 0.4,
        "timestamp": 0.3,
        "metadata": 0.3
    }
    
    # Minimum match score for fuzzy matching
    min_match_score: float = 0.8
    
    # Scheduler settings
    scheduler_enabled: bool = True
    scheduler_hour: int = 2  # 2 AM daily
    
    # File paths
    csv_upload_path: str = "uploads/recon/"
    
    class Config:
        env_file = ".env"
        env_prefix = "RECON_"

recon_settings = ReconSettings()