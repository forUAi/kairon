from datetime import date, datetime
from uuid import UUID, uuid4
from typing import Optional
import asyncpg
from app.database.connection import db_manager
from .recon_model import MatchResult, ReconStatus

class ReconLogger:
    """Handles database operations for reconciliation logging"""
    
    async def create_job(self, job_date: date, source_name: str) -> UUID:
        """Create a new reconciliation job entry"""
        job_id = uuid4()
        
        query = """
            INSERT INTO recon_jobs (
                id, job_date, source_name, status, started_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (job_date, source_name) 
            DO UPDATE SET 
                status = EXCLUDED.status,
                started_at = EXCLUDED.started_at,
                updated_at = NOW()
            RETURNING id
        """
        
        async with db_manager.get_connection() as conn:
            result = await conn.fetchrow(
                query, 
                job_id, 
                job_date, 
                source_name, 
                ReconStatus.RUNNING.value,
                datetime.now(),
                datetime.now()
            )
            
            return result['id']
    
    async def finalize_job(self, 
                          job_id: UUID, 
                          matched_count: int, 
                          unmatched_count: int,
                          total_external_txns: int = 0,
                          total_ledger_txns: int = 0,
                          status: str = "COMPLETED",
                          error_message: Optional[str] = None) -> None:
        """Finalize job with completion metrics"""
        
        query = """
            UPDATE recon_jobs 
            SET 
                status = $2,
                total_external_txns = $3,
                total_ledger_txns = $4,
                matched_count = $5,
                unmatched_count = $6,
                error_message = $7,
                completed_at = $8,
                updated_at = NOW()
            WHERE id = $1
        """
        
        async with db_manager.get_connection() as conn:
            await conn.execute(
                query,
                job_id,
                status,
                total_external_txns,
                total_ledger_txns,
                matched_count,
                unmatched_count,
                error_message,
                datetime.now()
            )
    
    async def log_result(self, 
                        job_date: date, 
                        source_name: str, 
                        result: MatchResult) -> None:
        """Log a single match result"""
        
        query = """
            INSERT INTO recon_logs (
                recon_date,
                source_name,
                external_txn_id,
                ledger_txn_id,
                matched,
                mismatch_reason,
                match_score,
                amount_difference,
                ledger_amount,
                external_amount,
                currency,
                timestamp_diff_seconds,
                metadata,
                created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
        """
        
        # Extract additional data from metadata if available
        metadata = result.metadata or {}
        ledger_amount = metadata.get('ledger_amount')
        external_amount = metadata.get('external_amount')
        currency = metadata.get('currency')
        
        async with db_manager.get_connection() as conn:
            await conn.execute(
                query,
                job_date,
                source_name,
                result.external_txn_id,
                result.ledger_txn_id,
                result.matched,
                result.mismatch_reason,
                result.match_score,
                result.amount_diff,
                ledger_amount,
                external_amount,
                currency,
                result.timestamp_diff_seconds,
                metadata,
                datetime.now()
            )
    
    async def get_job_status(self, job_date: date, source_name: Optional[str] = None):
        """Get job status for a specific date"""
        
        if source_name:
            query = """
                SELECT * FROM recon_jobs 
                WHERE job_date = $1 AND source_name = $2
                ORDER BY created_at DESC
            """
            params = [job_date, source_name]
        else:
            query = """
                SELECT * FROM recon_jobs 
                WHERE job_date = $1
                ORDER BY created_at DESC
            """
            params = [job_date]
        
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_recon_logs(self, 
                           job_date: date,
                           source_name: Optional[str] = None,
                           matched: Optional[bool] = None,
                           limit: int = 100,
                           offset: int = 0):
        """Get reconciliation logs with filtering"""
        
        conditions = ["recon_date = $1"]
        params = [job_date]
        param_count = 1
        
        if source_name:
            param_count += 1
            conditions.append(f"source_name = ${param_count}")
            params.append(source_name)
        
        if matched is not None:
            param_count += 1
            conditions.append(f"matched = ${param_count}")
            params.append(matched)
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT * FROM recon_logs 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count + 1} OFFSET ${param_count + 2}
        """
        
        params.extend([limit, offset])
        
        async with db_manager.get_connection() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]
    
    async def get_recon_summary(self, job_date: date, source_name: str):
        """Get reconciliation summary for a specific date and source"""
        
        query = """
            SELECT 
                COUNT(*) as total_logs,
                COUNT(*) FILTER (WHERE matched = true) as matched_count,
                COUNT(*) FILTER (WHERE matched = false) as unmatched_count,
                AVG(match_score) as avg_match_score,
                SUM(ABS(amount_difference)) as total_amount_variance,
                COUNT(DISTINCT external_txn_id) as unique_external_txns,
                COUNT(DISTINCT ledger_txn_id) as unique_ledger_txns
            FROM recon_logs
            WHERE recon_date = $1 AND source_name = $2
        """
        
        async with db_manager.get_connection() as conn:
            row = await conn.fetchrow(query, job_date, source_name)
            return dict(row) if row else None
    
    async def update_job_status(self, job_id: UUID, status: str, error_message: Optional[str] = None):
        """Update job status only"""
        
        query = """
            UPDATE recon_jobs 
            SET 
                status = $2,
                error_message = $3,
                updated_at = NOW()
            WHERE id = $1
        """
        
        async with db_manager.get_connection() as conn:
            await conn.execute(query, job_id, status, error_message)