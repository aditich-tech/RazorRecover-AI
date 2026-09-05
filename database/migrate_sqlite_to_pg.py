#!/usr/bin/env python3
"""
RazorRecover AI — SQLite to Supabase PostgreSQL Migration Script
Migrates all tables and existing records from local razor_recover.db to Supabase PostgreSQL.
Preserves IDs, timestamps, relationships, and sequences.
"""

import os
import sys
import sqlite3
from datetime import datetime

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import SQLITE_DB_PATH, DATABASE_URL, SUPABASE_DB_HOST
from database.db import get_db, init_db, query_db, execute_many

def run_migration():
    print("==================================================================")
    print("  RazorRecover AI: SQLite -> Supabase PostgreSQL Data Migration   ")
    print("==================================================================")

    # 1. Verify SQLite DB exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"[ERROR] SQLite database file '{SQLITE_DB_PATH}' not found!")
        sys.exit(1)

    # 2. Test PostgreSQL connection
    print("\n[Step 1/5] Verifying Supabase PostgreSQL connection...")
    try:
        with get_db() as pg_conn:
            with pg_conn.cursor() as cur:
                cur.execute("SELECT version();")
                pg_version = cur.fetchone()
                print(f"  [CONNECTED] Supabase PostgreSQL: {list(pg_version.values())[0][:60]}...")
    except Exception as e:
        print(f"\n[ERROR] Could not connect to Supabase PostgreSQL!")
        print(f"Details: {e}\n")
        print("Please check your .env file and ensure DATABASE_URL is properly configured.")
        print("Example: DATABASE_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres")
        sys.exit(1)

    # 3. Connect to SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # 4. Initialize PostgreSQL schema
    print("\n[Step 2/5] Initializing PostgreSQL schema in Supabase...")
    init_db(force_recreate=True)
    print("  [SUCCESS] Schema initialized (users, transactions, recovery_rules, audit_logs).")

    # 5. Migrate Users
    print("\n[Step 3/5] Migrating users table...")
    sqlite_cur.execute("SELECT id, email, password_hash, merchant_name, created_at FROM users")
    users = sqlite_cur.fetchall()
    user_records = [
        (u["id"], u["email"], u["password_hash"], u["merchant_name"], u["created_at"])
        for u in users
    ]
    if user_records:
        execute_many("""
            INSERT INTO users (id, email, password_hash, merchant_name, created_at)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                email = EXCLUDED.email,
                password_hash = EXCLUDED.password_hash,
                merchant_name = EXCLUDED.merchant_name
        """, user_records)
    print(f"  [MIGRATED] {len(user_records)} user record(s).")

    # 6. Migrate Recovery Rules
    print("\n[Step 4/5] Migrating recovery_rules table...")
    sqlite_cur.execute("""
        SELECT id, rule_id, rule_name, description, rule_type, condition_json, action_type, is_active, created_at
        FROM recovery_rules
    """)
    rules = sqlite_cur.fetchall()
    rule_records = [
        (r["id"], r["rule_id"], r["rule_name"], r["description"], r["rule_type"], r["condition_json"], r["action_type"], r["is_active"], r["created_at"])
        for r in rules
    ]
    if rule_records:
        execute_many("""
            INSERT INTO recovery_rules (id, rule_id, rule_name, description, rule_type, condition_json, action_type, is_active, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (rule_id) DO NOTHING
        """, rule_records)
    print(f"  [MIGRATED] {len(rule_records)} recovery rule(s).")

    # 7. Migrate Transactions in chunks of 1000
    print("\n[Step 5/5] Migrating transactions & audit_logs (streaming in batches)...")
    sqlite_cur.execute("SELECT COUNT(*) FROM transactions")
    total_txns = sqlite_cur.fetchone()[0]
    print(f"  Total transactions to migrate: {total_txns:,}")

    txn_insert_sql = """
        INSERT INTO transactions (
            id, transaction_id, customer_id, customer_name, customer_email,
            timestamp, amount, currency, payment_method,
            transaction_status, failure_reason, retry_count,
            previous_success_count, previous_failure_count, customer_success_rate,
            transaction_type, recovery_status, recovery_probability,
            recommended_action, recovery_attempts, recovered_amount,
            priority_score, explainability_notes, created_at, updated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (transaction_id) DO NOTHING
    """

    chunk_size = 1000
    offset = 0
    migrated_txns = 0

    while offset < total_txns:
        sqlite_cur.execute(f"""
            SELECT 
                id, transaction_id, customer_id, customer_name, customer_email,
                timestamp, amount, currency, payment_method,
                transaction_status, failure_reason, retry_count,
                previous_success_count, previous_failure_count, customer_success_rate,
                transaction_type, recovery_status, recovery_probability,
                recommended_action, recovery_attempts, recovered_amount,
                priority_score, explainability_notes, created_at, updated_at
            FROM transactions
            ORDER BY id ASC
            LIMIT {chunk_size} OFFSET {offset}
        """)
        rows = sqlite_cur.fetchall()
        if not rows:
            break

        chunk = [
            (
                r["id"], r["transaction_id"], r["customer_id"], r["customer_name"], r["customer_email"],
                r["timestamp"], float(r["amount"]), r["currency"], r["payment_method"],
                r["transaction_status"], r["failure_reason"], r["retry_count"],
                r["previous_success_count"], r["previous_failure_count"], float(r["customer_success_rate"] or 0.0),
                r["transaction_type"], r["recovery_status"], float(r["recovery_probability"] or 0.0),
                r["recommended_action"], r["recovery_attempts"], float(r["recovered_amount"] or 0.0),
                float(r["priority_score"] or 0.0), r["explainability_notes"], r["created_at"], r["updated_at"]
            )
            for r in rows
        ]
        execute_many(txn_insert_sql, chunk)
        migrated_txns += len(chunk)
        offset += chunk_size
        print(f"    -> Migrated {migrated_txns:,} / {total_txns:,} transactions...")

    # Migrate Audit Logs
    sqlite_cur.execute("SELECT COUNT(*) FROM audit_logs")
    total_logs = sqlite_cur.fetchone()[0]
    print(f"  Total audit logs to migrate: {total_logs:,}")

    audit_insert_sql = """
        INSERT INTO audit_logs (id, timestamp, transaction_id, customer_id, event_type, description, recovered_amount, actor)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    offset = 0
    migrated_logs = 0
    while offset < total_logs:
        sqlite_cur.execute(f"""
            SELECT id, timestamp, transaction_id, customer_id, event_type, description, recovered_amount, actor
            FROM audit_logs
            ORDER BY id ASC
            LIMIT {chunk_size} OFFSET {offset}
        """)
        rows = sqlite_cur.fetchall()
        if not rows:
            break

        chunk = [
            (
                r["id"], r["timestamp"], r["transaction_id"], r["customer_id"],
                r["event_type"], r["description"], float(r["recovered_amount"] or 0.0), r["actor"]
            )
            for r in rows
        ]
        execute_many(audit_insert_sql, chunk)
        migrated_logs += len(chunk)
        offset += chunk_size
        print(f"    -> Migrated {migrated_logs:,} / {total_logs:,} audit logs...")

    sqlite_conn.close()

    # Reset PostgreSQL sequences so next autoincrement IDs continue cleanly
    print("\n[Updating PostgreSQL sequences...]")
    with get_db() as pg_conn:
        with pg_conn.cursor() as cur:
            cur.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));")
            cur.execute("SELECT setval(pg_get_serial_sequence('recovery_rules', 'id'), COALESCE((SELECT MAX(id) FROM recovery_rules), 1));")
            cur.execute("SELECT setval(pg_get_serial_sequence('transactions', 'id'), COALESCE((SELECT MAX(id) FROM transactions), 1));")
            cur.execute("SELECT setval(pg_get_serial_sequence('audit_logs', 'id'), COALESCE((SELECT MAX(id) FROM audit_logs), 1));")

    # 8. Post-migration Verification
    print("\n==================================================================")
    print("                 POST-MIGRATION VERIFICATION                     ")
    print("==================================================================")
    u_cnt = query_db("SELECT COUNT(*) as cnt FROM users", one=True)["cnt"]
    r_cnt = query_db("SELECT COUNT(*) as cnt FROM recovery_rules", one=True)["cnt"]
    t_cnt = query_db("SELECT COUNT(*) as cnt FROM transactions", one=True)["cnt"]
    a_cnt = query_db("SELECT COUNT(*) as cnt FROM audit_logs", one=True)["cnt"]

    print(f"  Users:          SQLite = {len(users)} | Supabase = {u_cnt}")
    print(f"  Recovery Rules: SQLite = {len(rules)} | Supabase = {r_cnt}")
    print(f"  Transactions:   SQLite = {total_txns} | Supabase = {t_cnt}")
    print(f"  Audit Logs:     SQLite = {total_logs} | Supabase = {a_cnt}")

    if u_cnt == len(users) and r_cnt == len(rules) and t_cnt == total_txns and a_cnt == total_logs:
        print("\n[SUCCESS] 100% Data migration verified! All SQLite data is now active in Supabase PostgreSQL.")
    else:
        print("\n[WARNING] Row count mismatch! Please review output above.")

if __name__ == "__main__":
    run_migration()
