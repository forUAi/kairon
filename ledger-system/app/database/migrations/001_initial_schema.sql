-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Accounts table
CREATE TABLE accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    currency VARCHAR(3) NOT NULL,
    type VARCHAR(50) NOT NULL, -- 'user', 'internal', 'merchant'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Ledger events table (immutable event store)
CREATE TABLE ledger_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMP DEFAULT NOW(),
    source_account_id UUID REFERENCES accounts(id),
    destination_account_id UUID REFERENCES accounts(id),
    amount NUMERIC(18,6) NOT NULL,
    currency VARCHAR(3) NOT NULL,
    event_type VARCHAR(20) NOT NULL, -- 'DEBIT', 'CREDIT', 'TRANSFER'
    transaction_id UUID NOT NULL, -- Groups related debit/credit events
    metadata JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'SETTLED', -- 'PENDING', 'SETTLED', 'FAILED'
    created_at TIMESTAMP DEFAULT NOW()
);

-- Balance projections table
CREATE TABLE balances (
    account_id UUID PRIMARY KEY REFERENCES accounts(id),
    currency VARCHAR(3) NOT NULL,
    available_balance NUMERIC(18,6) DEFAULT 0,
    pending_balance NUMERIC(18,6) DEFAULT 0,
    last_updated TIMESTAMP DEFAULT NOW(),
    version INTEGER DEFAULT 1 -- For optimistic locking
);

-- Indexes for performance
CREATE INDEX idx_ledger_events_account_id ON ledger_events(source_account_id);
CREATE INDEX idx_ledger_events_destination_id ON ledger_events(destination_account_id);
CREATE INDEX idx_ledger_events_timestamp ON ledger_events(timestamp);
CREATE INDEX idx_ledger_events_transaction_id ON ledger_events(transaction_id);
CREATE INDEX idx_balances_currency ON balances(currency);

-- Constraints
ALTER TABLE ledger_events ADD CONSTRAINT check_amount_positive CHECK (amount > 0);
ALTER TABLE ledger_events ADD CONSTRAINT check_event_type CHECK (event_type IN ('DEBIT', 'CREDIT', 'TRANSFER'));
ALTER TABLE ledger_events ADD CONSTRAINT check_status CHECK (status IN ('PENDING', 'SETTLED', 'FAILED'));