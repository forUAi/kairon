-- Table: recon_jobs
CREATE TABLE IF NOT EXISTS recon_jobs (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED')),
    matched_count INTEGER DEFAULT 0,
    unmatched_count INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recon_jobs_date_source ON recon_jobs (created_at, source);


-- Table: recon_logs
CREATE TABLE IF NOT EXISTS recon_logs (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES recon_jobs(id) ON DELETE CASCADE,
    external_txn_id TEXT,
    ledger_txn_id TEXT,
    matched BOOLEAN,
    match_score NUMERIC,
    reason TEXT,
    amount_diff NUMERIC,
    currency TEXT,
    timestamp_diff_seconds INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recon_logs_job_id ON recon_logs (job_id);


-- Table: recon_summary (optional optimization table)
CREATE TABLE IF NOT EXISTS recon_summary (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES recon_jobs(id) ON DELETE CASCADE,
    match_rate NUMERIC,
    high_confidence_count INTEGER,
    low_confidence_count INTEGER,
    unmatched_count INTEGER,
    total_external_txns INTEGER,
    total_ledger_txns INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
