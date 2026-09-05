-- RazorRecover AI Database Schema (PostgreSQL / Supabase)

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    merchant_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    transaction_id VARCHAR(64) UNIQUE NOT NULL,
    customer_id VARCHAR(64) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    timestamp TIMESTAMP NOT NULL,
    amount DOUBLE PRECISION NOT NULL,
    currency VARCHAR(10) DEFAULT 'INR',
    payment_method VARCHAR(50) NOT NULL,
    transaction_status VARCHAR(50) NOT NULL,
    failure_reason VARCHAR(255),
    retry_count INTEGER DEFAULT 0,
    previous_success_count INTEGER DEFAULT 0,
    previous_failure_count INTEGER DEFAULT 0,
    customer_success_rate DOUBLE PRECISION DEFAULT 0.0,
    transaction_type VARCHAR(50) DEFAULT 'one_time',
    recovery_status VARCHAR(50) DEFAULT 'none',
    recovery_probability DOUBLE PRECISION DEFAULT 0.0,
    recommended_action VARCHAR(255),
    recovery_attempts INTEGER DEFAULT 0,
    recovered_amount DOUBLE PRECISION DEFAULT 0.0,
    priority_score DOUBLE PRECISION DEFAULT 0.0,
    explainability_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_txn_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_txn_status ON transactions(transaction_status);
CREATE INDEX IF NOT EXISTS idx_txn_recovery_status ON transactions(recovery_status);
CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_txn_payment_method ON transactions(payment_method);
CREATE INDEX IF NOT EXISTS idx_txn_failure_reason ON transactions(failure_reason);

CREATE TABLE IF NOT EXISTS recovery_rules (
    id SERIAL PRIMARY KEY,
    rule_id VARCHAR(64) UNIQUE NOT NULL,
    rule_name VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    rule_type VARCHAR(64) NOT NULL,
    condition_json TEXT NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    transaction_id VARCHAR(64) NOT NULL,
    customer_id VARCHAR(64) NOT NULL,
    event_type VARCHAR(64) NOT NULL,
    description TEXT NOT NULL,
    recovered_amount DOUBLE PRECISION DEFAULT 0.0,
    actor VARCHAR(255) DEFAULT 'RazorRecover AI Engine'
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_txn ON audit_logs(transaction_id);
CREATE INDEX IF NOT EXISTS idx_audit_customer ON audit_logs(customer_id);
