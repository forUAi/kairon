import asyncio
import uuid
from datetime import datetime, timedelta
from recon_engine.ledger.ledger_reader import LedgerTxn
from recon_engine.sources.csv_reader import ExternalTxn
from recon_engine.config import get_async_db
from recon_engine.database.models import ReconJob, ReconLog
from recon_engine.recon.recon_logger import ReconLogger

async def seed():
    db = await get_async_db()
    job_id = str(uuid.uuid4())

    now = datetime.utcnow()

    # Create fake internal ledger transactions
    ledger_txns = [
        LedgerTxn(txn_id="txn001", amount=100.00, timestamp=now - timedelta(minutes=5), currency="USD", metadata={"desc": "Ledger Payment"}),
        LedgerTxn(txn_id="txn002", amount=200.00, timestamp=now - timedelta(minutes=10), currency="USD", metadata={"desc": "Ledger Refund"}),
    ]

    # Create fake external transactions (CSV/API)
    external_txns = [
        ExternalTxn(txn_id="txn001", amount=100.00, timestamp=now - timedelta(minutes=5), currency="USD", metadata={"desc": "Bank Payment"}),
        ExternalTxn(txn_id="txn003", amount=205.00, timestamp=now - timedelta(minutes=8), currency="USD", metadata={"desc": "Bank Refund"}),
    ]

    print(f"✅ Seeding job_id: {job_id}")

    # Insert job
    await db.execute(
        ReconJob.insert().values(
            id=job_id,
            source="demo_seed",
            status="COMPLETED",
            matched_count=1,
            unmatched_count=1,
            started_at=now - timedelta(minutes=1),
            completed_at=now,
            created_at=now,
        )
    )

    # Insert logs (1 exact, 1 unmatched)
    await db.execute_many(
        ReconLog.insert(),
        [
            {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "external_txn_id": "txn001",
                "ledger_txn_id": "txn001",
                "matched": True,
                "match_score": 1.0,
                "reason": "Exact match",
                "amount_diff": 0.0,
                "currency": "USD",
                "timestamp_diff_seconds": 0,
                "created_at": now
            },
            {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "external_txn_id": "txn003",
                "ledger_txn_id": None,
                "matched": False,
                "match_score": 0.0,
                "reason": "No match found",
                "amount_diff": 205.0,
                "currency": "USD",
                "timestamp_diff_seconds": None,
                "created_at": now
            }
        ]
    )

    print("✅ Seed complete! You can now hit the summary and logs APIs.")

if __name__ == "__main__":
    asyncio.run(seed())
