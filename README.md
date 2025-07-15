# Smart Ledgering System

A production-ready, event-sourced double-entry ledger system designed for financial infrastructure, built using FastAPI and PostgreSQL.

---

##  Key Features

- **Double-Entry Accounting**: Every transaction creates matching debit/credit events.
- **Event Sourcing**: Immutable event log with full audit trail.
- **REST API**: FastAPI with endpoints for transfers, balances, and events.
- **PostgreSQL Backend**: Optimized schema with ACID compliance.
- **Comprehensive Testing**: Includes unit, integration, and API tests.
- **Docker Support**: Ready-to-run using Docker and `docker-compose`.
- **Modular Architecture**: Clean separation of concerns across all components.

---

##  Architecture Highlights

| Component            | Description                                              |
|----------------------|----------------------------------------------------------|
| **Command Processor** | Validates all business rules before processing           |
| **Event Store**       | Immutable, append-only log of transactions               |
| **Projection Engine** | Updates real-time balances from event stream             |
| **Repository Pattern**| Clean, abstracted access to database entities            |
| **PostgreSQL**        | Ensures transaction safety and indexing for performance  |

---

##  Getting Started

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd ledger-system
cp .env.example .env

### 2. Start with Docker

docker-compose up -d

### Seed Test Data
python scripts/seed_data.py

### Run Tests
pytest tests/ -v

### Access API Docs
Swagger: http://localhost:8000/docs

ReDoc: http://localhost:8000/redoc

Business Rules Enforced
Double-entry: Every debit has matching credit

No overdrafts (configurable)

Currency validation

Atomic transactions

Account existence validation

Positive amounts only

Sample Data Flow
The seed script demonstrates:

Internal Float → Alice (500 USD funding)

Alice → Bob (100 USD payment)

Bob → Alice (50 USD refund)

This creates a complete audit trail with proper double-entry bookkeeping.

API Examples
Create Account
curl -X POST "http://localhost:8000/ledger/account/" \
  -H "Content-Type: application/json" \
  -d '{
    "currency": "USD",
    "type": "user",
    "metadata": {"name": "John Doe"}
  }'

Transfer Funds
curl -X POST "http://localhost:8000/ledger/transfer/" \
  -H "Content-Type: application/json" \
  -d '{
    "source_account_id": "SOURCE_ID",
    "destination_account_id": "DEST_ID",
    "amount": "100.50",
    "currency": "USD",
    "metadata": {"description": "Payment for services"}
  }'

Get Account Balance
curl "http://localhost:8000/ledger/account/ACCOUNT_ID/balance"

Get Account Events
curl "http://localhost:8000/ledger/events/?account_id=ACCOUNT_ID&limit=50"

# Recon Engine – Modular Reconciliation System

A high-performance reconciliation engine designed to compare external transaction records (CSV/API) against internal ledger events and detect mismatches using exact and fuzzy logic.

---

## Key Features

- **Multi-Source Reconciliation**: Supports CSV, API, and custom adapters  
- **Event-Sourced Ledger Integration**: Works with append-only double-entry ledgers  
- **Matching Engine**: Exact and fuzzy logic with configurable thresholds  
- **FastAPI-Driven**: APIs for triggering, monitoring, and debugging jobs  
- **PostgreSQL Backend**: Optimized schema with job tracking and log indexing  
- **Job Scheduler**: Runs reconciliation daily at configured hour  
- **Modular CLI**: Run reconciliation manually from terminal  
- **Async Python**: Built with asyncio, asyncpg, and FastAPI  
- **Comprehensive Testing**: Unit and integration tests for full flow  

---

## Architecture Overview

| Component       | Role                                                       |
|------------------|------------------------------------------------------------|
| ReconEngine      | Orchestrates job lifecycle: load, match, log, finalize     |
| LedgerReader     | Pulls internal transactions from the smart ledger          |
| CSVReader        | Reads external records from CSV                            |
| APIAdapter       | Pulls external records via API                              |
| ExactMatcher     | Matches by txn_id, amount, timestamp                        |
| FuzzyMatcher     | Threshold-based match scoring                               |
| ReconLogger      | Logs matches, updates jobs, writes summary                 |
| FastAPI Router   | APIs: /run, /status, /logs, /summary                        |
| Scheduler        | Runs reconciliation jobs daily at configured hour          |
| PostgreSQL       | Stores jobs, logs, summaries                                |
| CLI Tool         | Trigger manually: python cli.py run-recon --source ...     |

---

## Setup Instructions

### Clone & Configure

```bash
git clone https://github.com/your-org/recon_engine.git
cd recon_engine
cp .env.example .env
```

### Start with Docker

```bash
docker-compose up -d
```

### Run Migrations (Manual Alternative)

```bash
psql -U postgres -d recon_db -f recon_engine/database/schema.sql
```

### Trigger Reconciliation (CLI)

```bash
python recon_engine/cli.py run-recon \
  --source bank_csv \
  --date 2025-07-13 \
  --file_path ./data/bank_dump.csv
```

---

## API Endpoints

### Trigger Reconciliation

```bash
curl -X POST "http://localhost:8000/recon/run" \
  -H "Content-Type: application/json" \
  -d '{ "source": "bank_csv", "date": "2025-07-13" }'
```

### Get Job Status

```bash
curl http://localhost:8000/recon/status/2025-07-13
```

### View Logs

```bash
curl "http://localhost:8000/recon/logs?source=bank_csv&date=2025-07-13&matched=false"
```

### View Summary

```bash
curl http://localhost:8000/recon/summary/2025-07-13
```

---

## Testing

```bash
pytest tests/ -v
```

- `test_matchers.py`: Matcher logic (exact + fuzzy)  
- `test_recon_engine.py`: Full job flow with mocks  

---

## Business Rules Enforced

- Txn IDs must match or meet fuzzy scoring threshold  
- Amounts must be within allowed difference  
- Timestamps must be within allowable window  
- Only supported currencies accepted  
- All logs retained for audit/compliance  

---

## Sample Data Flow

- External CSV has 3 transactions  
- Internal ledger has 3 events  

**ReconEngine:**

- Matches 2 exactly  
- Fuzzy matches 1 with score 0.87  

Logs, summaries, and job status are recorded in PostgreSQL.

---

## Security and Compliance

- Immutable audit log per job  
- Can be integrated with Vault/JWT for secure auth  
- Logs contain timestamps, match scores, and reasons for mismatches  

---

## Developer Tools

### Dev Environment

```bash
poetry install
poetry run uvicorn recon_engine.api.main:app --reload
```

### API Docs

- Swagger UI: http://localhost:8000/docs  
- ReDoc: http://localhost:8000/redoc

---

## Future Extensions

- Support for S3, Snowflake, BigQuery sources  
- ML-powered anomaly detection module  
- Integration with ledger replay engine  
- Alerts for unmatched or anomalous records  

---

## License

MIT — Free to use, modify, and embed in enterprise systems.

---

## Author

Built by Vishal as part of the Kairon financial infrastructure stack.