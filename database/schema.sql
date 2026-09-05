-- RazorRecover AI Database Schema (SQLite)

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    merchant_name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT UNIQUE NOT NULL,
    customer_id TEXT NOT NULL,
    customer_name TEXT NOT NULL,
    customer_email TEXT,
    timestamp DATETIME NOT NULL,
    amount REAL NOT NULL,
    currency TEXT DEFAULT 'INR',
    payment_method TEXT NOT NULL, -- UPI, Credit Card, Debit Card, Net Banking, Wallet
    transaction_status TEXT NOT NULL, -- success, failed, pending, abandoned, recovered
    failure_reason TEXT, -- Insufficient Funds, Bank Decline, Payment Timeout, UPI Failure, Card Declined, Authentication Failure, Network Error
    retry_count INTEGER DEFAULT 0,
    previous_success_count INTEGER DEFAULT 0,
    previous_failure_count INTEGER DEFAULT 0,
    customer_success_rate REAL DEFAULT 0.0,
    transaction_type TEXT DEFAULT 'one_time', -- one_time, subscription, recurring, checkout
    recovery_status TEXT DEFAULT 'none', -- none, pending_analysis, eligible, in_progress, recovered, retry_failed, stopped
    recovery_probability REAL DEFAULT 0.0,
    recommended_action TEXT, -- Smart Retry, Intelligent Retry Timing, Payment Reminder, Alternate Payment Route
    recovery_attempts INTEGER DEFAULT 0,
    recovered_amount REAL DEFAULT 0.0,
    priority_score REAL DEFAULT 0.0,
    explainability_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_txn_customer ON transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_txn_status ON transactions(transaction_status);
CREATE INDEX IF NOT EXISTS idx_txn_recovery_status ON transactions(recovery_status);
CREATE INDEX IF NOT EXISTS idx_txn_timestamp ON transactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_txn_payment_method ON transactions(payment_method);
CREATE INDEX IF NOT EXISTS idx_txn_failure_reason ON transactions(failure_reason);

CREATE TABLE IF NOT EXISTS recovery_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT UNIQUE NOT NULL,
    rule_name TEXT NOT NULL,
    description TEXT NOT NULL,
    rule_type TEXT NOT NULL, -- smart_retry, upi_optimization, high_value, stopping_rule, custom
    condition_json TEXT NOT NULL,
    action_type TEXT NOT NULL, -- SMART_RETRY, TIMED_RETRY, PAYMENT_REMINDER, ROUTE_SWITCH, STOP
    is_active INTEGER DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    transaction_id TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    event_type TEXT NOT NULL, -- AI_IDENTIFIED, RECOMMENDED_ACTION, MERCHANT_APPROVED, WORKFLOW_EXECUTED, PAYMENT_RECOVERED, STOPPING_RULE_APPLIED
    description TEXT NOT NULL,
    recovered_amount REAL DEFAULT 0.0,
    actor TEXT DEFAULT 'RazorRecover AI Engine'
);

CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_txn ON audit_logs(transaction_id);
CREATE INDEX IF NOT EXISTS idx_audit_customer ON audit_logs(customer_id);
