Key Features 
✅ Double-Entry Accounting: Every transaction creates matching debit/credit events
✅ Event Sourcing: Immutable event log with full audit trail
✅ REST API: FastAPI with endpoints for transfers, balances, and events
✅ PostgreSQL Backend: Optimized schema with proper indexes
✅ Comprehensive Testing: Unit, integration, and API tests
✅ Docker Support: Ready-to-run with docker-compose
✅ Modular Architecture: Clean separation of concerns
🏗️ Architecture Highlights

Command Processor: Validates all business rules before execution
Event Store: Immutable append-only event logging
Projection Engine: Real-time balance updates from events
Repository Pattern: Clean data access abstractions
Transaction Safety: ACID compliance with PostgreSQL transactions

# Clone and setup
git clone <your-repo>
cd ledger-system
cp .env.example .env

# Start with Docker
docker-compose up -d

# Seed test data
python scripts/seed_data.py

# Run tests
pytest tests/ -v

# Access API docs
open http://localhost:8000/docs

Business Rules Enforced

✅ Double-entry: Every debit has matching credit
✅ No overdrafts (configurable)
✅ Currency validation
✅ Atomic transactions
✅ Account existence validation
✅ Positive amounts only

📊 Sample Data Flow
The seed script demonstrates the three scenarios you requested:

Internal Float → Alice (500 USD funding)
Alice → Bob (100 USD payment)
Bob → Alice (50 USD refund)

This creates a complete audit trail with proper double-entry bookkeeping!


📚 API Documentation
Example API Calls
##Create Account
bash
curl -X POST "http://localhost:8000/ledger/account/" \
  -H "Content-Type: application/json" \
  -d '{
    "currency": "USD",
    "type": "user",
    "metadata": {"name": "John Doe"}
  }'
  
##Transfer Funds
bash
curl -X POST "http://localhost:8000/ledger/transfer/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "550e8400-e29b-41d4-a716-446655440000",
    "destination_account_id": "550e8400-e29b-41d4-a716-446655440001",
    "amount": "100.50",
    "currency": "USD",
    "metadata": {"description": "Payment for services"}
  }'
  
##Get Account Balance
bash
curl "http://localhost:8000/ledger/account/550e8400-e29b-41d4-a716-446655440000/balance"

##Get Account Events
bash
curl "http://localhost:8000/ledger/events/?account_id=550e8400-e29b-41d4-a716-446655440000&limit=50"

🚀 Getting Started

Setup Environment
bash
cp .env.example .env

# Edit .env with your configuration

Start with Docker
bashdocker-compose up -d

Run Migrations
bash# Migrations run automatically with docker-compose
# Or manually: psql -U ledger_user -d ledger_db -f app/database/migrations/001_initial_schema.sql

Seed Data
bashpython scripts/seed_data.py

Run Tests
bashpytest tests/ -v

Access API Documentation

OpenAPI/Swagger: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc


# 🧠 Recon Engine – Modular Reconciliation System

A high-performance, event-sourced reconciliation engine designed for financial infrastructure. Built to compare external transactions (bank, CSV, API) with internal ledger events, detect mismatches, and generate a complete audit trail — with APIs, match scoring, summaries, and automation built-in.

---

## ✅ Key Features

- ✅ **Multi-Source Reconciliation**: Supports CSV, API, and custom source adapters
- ✅ **Event-Sourced Ledger Integration**: Designed to work with append-only double-entry ledgers
- ✅ **Matching Engine**: Exact + Fuzzy logic with configurable thresholds
- ✅ **FastAPI-Driven**: Rich APIs for triggering, monitoring, and debugging reconciliation jobs
- ✅ **PostgreSQL Backend**: Optimized schema with job tracking and log indexing
- ✅ **Job Scheduler**: Auto-runs reconciliation daily at a defined hour
- ✅ **Modular CLI**: Manually trigger reconciliation from the terminal
- ✅ **Async Python**: Built fully with `asyncio`, `asyncpg`, and `FastAPI`
- ✅ **Comprehensive Testing**: Unit tests for matchers + integration tests for full job flow

---

## 🏗️ Architecture Highlights

| Component           | Role |
|---------------------|------|
| `ReconEngine`       | Orchestrates job lifecycle: load, match, log, finalize |
| `LedgerReader`      | Pulls internal transactions from the smart ledger |
| `CSVReader` / `APIAdapter` | Pulls external records |
| `ExactMatcher`      | Direct match by txn_id, amount, timestamp |
| `FuzzyMatcher`      | Threshold-based matching with scoring |
| `ReconLogger`       | Logs matches, updates jobs, writes summary |
| `FastAPI Router`    | Provides `/run`, `/status`, `/logs`, `/summary` |
| `Scheduler`         | Async loop to run jobs daily at configured hour |
| `PostgreSQL`        | Stores jobs, logs, summaries |
| `CLI Tool`          | One-liner trigger: `python cli.py run-recon --source ...` |

---

## 🚀 Getting Started

### 1️⃣ Clone & Setup

```bash
git clone https://github.com/your-org/recon_engine.git
cd recon_engine
cp .env.example .env

2️⃣ Start with Docker
bash
Copy
Edit
docker-compose up -d
Runs API server + Postgres + Alembic migrations.

3️⃣ Run Migrations (if manual)
bash
Copy
Edit
psql -U postgres -d recon_db -f recon_engine/database/schema.sql
🧪 Run Reconciliation via CLI
bash
Copy
Edit
python recon_engine/cli.py run-recon \
  --source bank_csv \
  --date 2025-07-13 \
  --file_path ./data/bank_dump.csv
⚙️ API Endpoints
✅ Trigger Reconciliation
bash
Copy
Edit
curl -X POST "http://localhost:8000/recon/run" \
  -H "Content-Type: application/json" \
  -d '{ "source": "bank_csv", "date": "2025-07-13" }'
✅ Get Job Status
bash
Copy
Edit
curl http://localhost:8000/recon/status/2025-07-13
✅ View Logs (Matched/Unmatched)
bash
Copy
Edit
curl "http://localhost:8000/recon/logs?source=bank_csv&date=2025-07-13&matched=false"
✅ Job Summary
bash
Copy
Edit
curl http://localhost:8000/recon/summary/2025-07-13
🧪 Testing
Run Tests
bash
Copy
Edit
pytest tests/ -v
Tests include:

✅ test_matchers.py: Exact & fuzzy matcher logic

✅ test_recon_engine.py: Full job flow with mocks

💡 Business Rules Enforced
✅ Txn IDs must match or pass fuzzy scoring threshold

✅ Amounts must be within allowed_amount_diff

✅ Timestamps must be within max_time_diff_minutes

✅ Only supported currencies are accepted

✅ All results logged for compliance and auditability

📊 Sample Data Flow
text
Copy
Edit
🔁 External CSV (bank) with 3 txns
🔁 Internal ledger with 3 events

🎯 ReconEngine:
  → Matches 2 exactly
  → Fuzzy matches 1 with score 0.87

🧾 Logs written to recon_logs
📊 Summary written to recon_summary
📥 Job status updated in recon_jobs
🛡️ Security and Compliance
🔒 Full audit trail per job (immutable log records)

🔐 Can be integrated with Vault/JWT for secure token auth

📁 Logs stored with timestamp, score, and mismatch reason

🧰 Developer Tools
Dev Environment
bash
Copy
Edit
poetry install
poetry run uvicorn recon_engine.api.main:app --reload
API Docs
Swagger UI: http://localhost:8000/docs

Redoc: http://localhost:8000/redoc

📦 Future Extensions
📁 S3 / Snowflake / BigQuery support as sources

🧠 ML-powered anomaly detector module

🧩 Integration with ledger replay engine for real-time validation

📤 Alerts for unmatched records

👨‍💻 Author
Built with ❤️ by Vishal, part of the Kairon Infra stack.

🏁 License
MIT — Free to use, modify, and embed in enterprise financial workflows.


