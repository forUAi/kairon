from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from pydantic import BaseModel
from datetime import date
from typing import Optional, List, Dict, Any
from uuid import UUID
import logging

from ..recon.recon_engine import ReconEngine
from ..recon.recon_logger import ReconLogger
from ..recon.recon_model import ReconStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recon", tags=["reconciliation"])

# Pydantic models for request/response
class RunReconRequest(BaseModel):
    date: date
    source: str
    file_path: Optional[str] = None
    base_url: Optional[str] = None
    auth_token: Optional[str] = None

class RunReconResponse(BaseModel):
    job_id: UUID
    status: str
    message: str

class JobStatusResponse(BaseModel):
    id: UUID
    job_date: date
    source_name: str
    status: str
    total_external_txns: int
    total_ledger_txns: int
    matched_count: int
    unmatched_count: int
    error_message: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    created_at: str

class ReconLogResponse(BaseModel):
    id: UUID
    recon_date: date
    source_name: str
    external_txn_id: Optional[str]
    ledger_txn_id: Optional[UUID]
    matched: bool
    mismatch_reason: Optional[str]
    match_score: float
    amount_difference: float
    ledger_amount: Optional[float]
    external_amount: Optional[float]
    currency: Optional[str]
    timestamp_diff_seconds: Optional[int]
    metadata: Dict[str, Any]
    created_at: str

class ReconSummaryResponse(BaseModel):
    total_logs: int
    matched_count: int
    unmatched_count: int
    match_rate: float
    avg_match_score: float
    total_amount_variance: float
    unique_external_txns: int
    unique_ledger_txns: int

# Initialize engine and logger
recon_engine = ReconEngine()
recon_logger = ReconLogger()

@router.post("/run", response_model=RunReconResponse)
async def run_reconciliation(request: RunReconRequest, background_tasks: BackgroundTasks):
    """
    Start a reconciliation job for the specified date and source
    """
    try:
        # Validate source configuration
        kwargs = {}
        if request.file_path:
            kwargs['file_path'] = request.file_path
        if request.base_url:
            kwargs['base_url'] = request.base_url
        if request.auth_token:
            kwargs['auth_token'] = request.auth_token
        
        # Validate source config
        is_valid = await recon_engine.validate_source_config(request.source, **kwargs)
        if not is_valid:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid configuration for source '{request.source}'"
            )
        
        # Start reconciliation job in background
        job_id = await recon_engine.run(request.date, request.source, **kwargs)
        
        return RunReconResponse(
            job_id=job_id,
            status=ReconStatus.COMPLETED.value,
            message=f"Reconciliation job completed successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to start reconciliation job: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start reconciliation: {str(e)}"
        )

@router.get("/status/{target_date}", response_model=List[JobStatusResponse])
async def get_job_status(target_date: date, source: Optional[str] = None):
    """
    Get reconciliation job status for a specific date
    """
    try:
        jobs = await recon_logger.get_job_status(target_date, source)
        
        return [
            JobStatusResponse(
                id=job['id'],
                job_date=job['job_date'],
                source_name=job['source_name'],
                status=job['status'],
                total_external_txns=job['total_external_txns'] or 0,
                total_ledger_txns=job['total_ledger_txns'] or 0,
                matched_count=job['matched_count'] or 0,
                unmatched_count=job['unmatched_count'] or 0,
                error_message=job['error_message'],
                started_at=job['started_at'].isoformat() if job['started_at'] else None,
                completed_at=job['completed_at'].isoformat() if job['completed_at'] else None,
                created_at=job['created_at'].isoformat()
            )
            for job in jobs
        ]
        
    except Exception as e:
        logger.error(f"Failed to get job status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@router.get("/logs", response_model=List[ReconLogResponse])
async def get_reconciliation_logs(
    date: date = Query(..., description="Date to filter logs"),
    source: Optional[str] = Query(None, description="Source name to filter"),
    matched: Optional[bool] = Query(None, description="Filter by match status"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records"),
    offset: int = Query(0, ge=0, description="Number of records to skip")
):
    """
    Get reconciliation logs with optional filtering
    """
    try:
        logs = await recon_logger.get_recon_logs(
            job_date=date,
            source_name=source,
            matched=matched,
            limit=limit,
            offset=offset
        )
        
        return [
            ReconLogResponse(
                id=log['id'],
                recon_date=log['recon_date'],
                source_name=log['source_name'],
                external_txn_id=log['external_txn_id'],
                ledger_txn_id=log['ledger_txn_id'],
                matched=log['matched'],
                mismatch_reason=log['mismatch_reason'],
                match_score=log['match_score'],
                amount_difference=float(log['amount_difference']),
                ledger_amount=float(log['ledger_amount']) if log['ledger_amount'] else None,
                external_amount=float(log['external_amount']) if log['external_amount'] else None,
                currency=log['currency'],
                timestamp_diff_seconds=log['timestamp_diff_seconds'],
                metadata=log['metadata'] or {},
                created_at=log['created_at'].isoformat()
            )
            for log in logs
        ]
        
    except Exception as e:
        logger.error(f"Failed to get reconciliation logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get reconciliation logs: {str(e)}"
        )

@router.get("/summary/{target_date}/{source}", response_model=ReconSummaryResponse)
async def get_reconciliation_summary(target_date: date, source: str):
    """
    Get reconciliation summary for a specific date and source
    """
    try:
        summary = await recon_logger.get_recon_summary(target_date, source)
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"No reconciliation data found for {target_date} and source {source}"
            )
        
        match_rate = 0.0
        if summary['total_logs'] > 0:
            match_rate = summary['matched_count'] / summary['total_logs']
        
        return ReconSummaryResponse(
            total_logs=summary['total_logs'],
            matched_count=summary['matched_count'],
            unmatched_count=summary['unmatched_count'],
            match_rate=match_rate,
            avg_match_score=float(summary['avg_match_score'] or 0),
            total_amount_variance=float(summary['total_amount_variance'] or 0),
            unique_external_txns=summary['unique_external_txns'],
            unique_ledger_txns=summary['unique_ledger_txns']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get reconciliation summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get reconciliation summary: {str(e)}"
        )

@router.get("/sources", response_model=List[str])
async def get_available_sources():
    """
    Get list of available reconciliation sources
    """
    try:
        sources = await recon_engine.get_available_sources()
        return sources
        
    except Exception as e:
        logger.error(f"Failed to get available sources: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get available sources: {str(e)}"
        )

@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: UUID):
    """
    Cancel a running reconciliation job
    """
    try:
        await recon_logger.update_job_status(
            job_id, 
            ReconStatus.FAILED.value, 
            "Job cancelled by user"
        )
        
        return {"message": f"Job {job_id} cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Failed to cancel job {job_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel job: {str(e)}"
        )

@router.post("/validate-source")
async def validate_source_configuration(request: RunReconRequest):
    """
    Validate source configuration without running reconciliation
    """
    try:
        kwargs = {}
        if request.file_path:
            kwargs['file_path'] = request.file_path
        if request.base_url:
            kwargs['base_url'] = request.base_url
        if request.auth_token:
            kwargs['auth_token'] = request.auth_token
        
        is_valid = await recon_engine.validate_source_config(request.source, **kwargs)
        
        return {
            "valid": is_valid,
            "source": request.source,
            "message": "Configuration is valid" if is_valid else "Configuration is invalid"
        }
        
    except Exception as e:
        logger.error(f"Failed to validate source configuration: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate source configuration: {str(e)}"
        )