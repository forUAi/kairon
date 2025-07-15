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
