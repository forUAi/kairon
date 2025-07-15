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
