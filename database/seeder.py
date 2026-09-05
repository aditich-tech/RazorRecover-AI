import os
import sys
import random
import hashlib
from datetime import datetime, timedelta

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import get_db, execute_many, query_db, execute_db


FIRST_NAMES = [
    "Aarav", "Aditi", "Rohan", "Priya", "Vikram", "Ananya", "Rahul", "Neha",
    "Siddharth", "Pooja", "Arjun", "Kavita", "Amit", "Sneha", "Karan", "Divya",
    "Manish", "Ritu", "Deepak", "Swati", "Suresh", "Meera", "Rajesh", "Sunita",
    "Gaurav", "Anjali", "Naveen", "Shreya", "Varun", "Tanvi", "Akash", "Isha",
    "Harsh", "Pallavi", "Nikhil", "Simran", "Pranav", "Aarti", "Alok", "Preeti"
]

LAST_NAMES = [
    "Sharma", "Verma", "Patel", "Gupta", "Mehta", "Singh", "Reddy", "Kumar",
    "Joshi", "Chopra", "Nair", "Iyer", "Rao", "Malhotra", "Bhatia", "Deshmukh",
    "Saxena", "Agarwal", "Bansal", "Chatterjee", "Mishra", "Trivedi", "Kapoor", "Pandey"
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"]
PAYMENT_METHOD_WEIGHTS = [0.48, 0.24, 0.16, 0.08, 0.04]

FAILURE_REASONS = [
    "Insufficient Funds",
    "Bank Decline",
    "Payment Timeout",
    "UPI Failure",
    "Card Declined",
    "Authentication Failure",
    "Network Error"
]

TRANSACTION_TYPES = ["one_time", "subscription", "recurring", "checkout"]
COMMON_AMOUNTS = [
    499, 799, 999, 1299, 1499, 1999, 2499, 2999, 3499, 4999,
    5999, 7499, 8500, 9999, 12000, 15000, 18500, 24999, 35000, 48000
]

def generate_customers(num_customers=700):
    customers = []
    for i in range(1, num_customers + 1):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        c_id = f"CUST-{1000 + i}"
        name = f"{first} {last}"
        email = f"{first.lower()}.{last.lower()}{i}@example.com"
        
        # Customer Persona
        persona = random.choices(
            ["high_loyalty", "upi_shopper", "subscription", "budget_sensitive", "new_user"],
            weights=[0.30, 0.35, 0.15, 0.12, 0.08]
        )[0]
        
        customers.append({
            "customer_id": c_id,
            "name": name,
            "email": email,
            "persona": persona
        })
    return customers

def compute_recovery_scoring(amount, payment_method, failure_reason, retry_count, success_rate, customer_history_success_count):
    """
    Explainable AI Scoring Engine for initial probability and recommendation.
    """
    score = 0.50  # baseline
    reasons = []
    
    # 1. Failure reason base potential
    if failure_reason in ["Payment Timeout", "Network Error"]:
        score += 0.28
        reasons.append(f"{failure_reason} is typically a transient gateway failure with high retry recovery rate")
    elif failure_reason == "UPI Failure":
        score += 0.22
        reasons.append("UPI failures historically yield 78% recovery when re-queried or timed appropriately")
    elif failure_reason == "Bank Decline":
        score += 0.05
        reasons.append("Bank decline may require alternative routing or updated auth")
    elif failure_reason == "Insufficient Funds":
        score -= 0.15
        reasons.append("Insufficient funds requires automated payment reminder after grace period")
    elif failure_reason in ["Card Declined", "Authentication Failure"]:
        score -= 0.10
        reasons.append("Card/Auth decline requires fresh OTP or alternate payment route")
        
    # 2. Customer history
    if success_rate >= 0.75:
        score += 0.18
        reasons.append(f"Customer has a stellar track record ({int(success_rate*100)}% historical payment success)")
    elif success_rate >= 0.50:
        score += 0.08
        reasons.append("Customer has moderate payment reliability")
    elif success_rate < 0.30 and customer_history_success_count > 0:
        score -= 0.12
        reasons.append("Customer exhibits high frequency of past payment dropoffs")
        
    # 3. Retry count decay
    if retry_count == 0:
        score += 0.10
        reasons.append("First-time failure: optimal window for Smart Retry")
    elif retry_count == 1:
        score += 0.05
        reasons.append("Second attempt statistically recovers 64% of transient failures")
    elif retry_count >= 2:
        score -= 0.22
        reasons.append(f"Prior {retry_count} retries failed; diminishing return on direct retry")
        
    # 4. Payment method factor
    if payment_method == "UPI":
        score += 0.05
    elif payment_method == "Net Banking":
        score -= 0.04
        
    # Bound between 0.05 and 0.98
    prob = round(max(0.08, min(0.96, score)), 2)
    
    # Determine Recommended Action
    if prob >= 0.75:
        if retry_count <= 1 and failure_reason in ["Payment Timeout", "Network Error", "UPI Failure"]:
            action = "Smart Retry"
        else:
            action = "Intelligent Retry Timing"
    elif prob >= 0.45:
        if failure_reason in ["Insufficient Funds"]:
            action = "Payment Reminder"
        elif failure_reason in ["Bank Decline", "Card Declined"]:
            action = "Alternate Payment Route"
        else:
            action = "Intelligent Retry Timing"
    else:
        action = "Alternate Payment Route" if failure_reason in ["Bank Decline", "Card Declined"] else "Payment Reminder"
        
    # Priority score = prob * log(amount) factor
    amount_weight = min(1.8, max(0.8, amount / 5000.0))
    priority_score = round(prob * amount_weight * 100, 1)
    
    return prob, action, priority_score, " · ".join(reasons[:3])

def seed_database():
    """Generates 10,000+ realistic transaction records with customer histories."""
    print("Initiating RazorRecover AI database seeding...")
    customers = generate_customers(num_customers=750)
    
    # Pre-seed users
    pwd_hash = hashlib.sha256("demo123".encode()).hexdigest()
    execute_db("""
        INSERT INTO users (id, email, password_hash, merchant_name)
        VALUES (1, 'merchant@razorpay.com', %s, 'Razorpay Prime Merchant Demo')
        ON CONFLICT (id) DO UPDATE SET 
            email = EXCLUDED.email, 
            password_hash = EXCLUDED.password_hash, 
            merchant_name = EXCLUDED.merchant_name
    """, (pwd_hash,))
    
    # Pre-seed default recovery rules
    rules = [
        ("RULE-01", "Smart Retry Engine", "Automatically retry eligible transient failures (timeouts, network errors) when recovery probability is >70%.", "smart_retry", '{"min_probability": 0.70, "allowed_failures": ["Payment Timeout", "Network Error", "UPI Failure"]}', "SMART_RETRY", 1),
        ("RULE-02", "Intelligent UPI Timing", "Schedule UPI retries during high bank TPS windows (avoiding 1–3 PM peak congestion).", "upi_optimization", '{"payment_method": "UPI", "optimal_window": "off_peak"}', "TIMED_RETRY", 1),
        ("RULE-03", "High-Value Payment Guard", "Apply multi-channel SMS & WhatsApp payment links for orders over ₹10,000.", "high_value", '{"min_amount": 10000}', "PAYMENT_REMINDER", 1),
        ("RULE-04", "Max Retry Cap (Stopping Rule)", "Strictly halt recovery workflows after 3 consecutive attempts to prevent customer fatigue.", "stopping_rule", '{"max_retries": 3}', "STOP", 1),
        ("RULE-05", "Low Probability Threshold (Stopping Rule)", "Do not attempt automated recovery if AI probability is below 25% without manual override.", "stopping_rule", '{"min_probability": 0.25}', "STOP", 1),
        ("RULE-06", "Trust Customers", "Retry/resolve a failed payment only when that customer's historical success rate is 75% or higher.", "trust_customers", '{"min_customer_success_rate": 0.75}', "SMART_RETRY", 1)
    ]
    
    execute_many("""
        INSERT INTO recovery_rules (rule_id, rule_name, description, rule_type, condition_json, action_type, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (rule_id) DO NOTHING
    """, rules)

    # Generate multi-transaction customer journeys over 90 days
    now = datetime.now()
    transactions = []
    audit_logs = []
    
    txn_counter = 10000
    total_target = 10500
    
    # Customer state tracking
    customer_stats = {
        c["customer_id"]: {
            "success": 0,
            "failed": 0,
            "history": []
        } for c in customers
    }
    
    # Allocate transactions per customer based on persona
    # Total allocations will meet or exceed total_target
    txn_plan = []
    for c in customers:
        p = c["persona"]
        if p == "high_loyalty":
            count = random.randint(22, 45)
        elif p == "upi_shopper":
            count = random.randint(14, 28)
        elif p == "subscription":
            count = random.randint(8, 18)
        elif p == "budget_sensitive":
            count = random.randint(6, 14)
        else: # new_user
            count = random.randint(2, 6)
        
        for _ in range(count):
            txn_plan.append(c)
            
    random.shuffle(txn_plan)
    # Trim or expand to total_target
    if len(txn_plan) < total_target:
        while len(txn_plan) < total_target:
            txn_plan.append(random.choice(customers))
    else:
        txn_plan = txn_plan[:total_target]
        
    # Assign timestamps across the past 90 days
    # Weight timestamps slightly higher in recent 14 days to simulate a thriving active merchant
    start_date = now - timedelta(days=90)
    total_days = 90
    
    records_to_insert = []
    
    for idx, c in enumerate(txn_plan):
        txn_counter += 1
        txn_id = f"pay_{txn_counter:07d}"
        c_id = c["customer_id"]
        c_name = c["name"]
        c_email = c["email"]
        c_persona = c["persona"]
        
        # Calculate timestamp with recent clustering
        day_offset = random.choices(
            range(total_days),
            weights=[1.0 + (i / total_days) * 2.0 for i in range(total_days)]
        )[0]
        hour = random.randint(8, 23)
        minute = random.randint(0, 59)
        second = random.randint(0, 59)
        txn_time = start_date + timedelta(days=day_offset, hours=hour, minutes=minute, seconds=second)
        
        # Amount based on persona
        if c_persona == "high_loyalty":
            amount = random.choice(COMMON_AMOUNTS[6:]) # ₹8,500 - ₹48,000
        elif c_persona == "upi_shopper":
            amount = random.choice(COMMON_AMOUNTS[:7]) # ₹499 - ₹2,499
        elif c_persona == "subscription":
            amount = random.choice([999, 1499, 2499, 4999])
        else:
            amount = random.choice(COMMON_AMOUNTS)
            
        # Payment method
        if c_persona == "upi_shopper":
            method = "UPI" if random.random() < 0.85 else random.choice(PAYMENT_METHODS)
        else:
            method = random.choices(PAYMENT_METHODS, weights=PAYMENT_METHOD_WEIGHTS)[0]
            
        txn_type = "subscription" if c_persona == "subscription" else "one_time"
        
        # Current customer statistics before this transaction
        prev_success = customer_stats[c_id]["success"]
        prev_failed = customer_stats[c_id]["failed"]
        total_prev = prev_success + prev_failed
        success_rate = round(prev_success / total_prev, 2) if total_prev > 0 else 0.85
        
        # Determine success vs failure
        # Personas have characteristic base failure rates
        if c_persona == "high_loyalty":
            fail_prob = 0.10
        elif c_persona == "upi_shopper":
            fail_prob = 0.22
        elif c_persona == "budget_sensitive":
            fail_prob = 0.38
        else:
            fail_prob = 0.18
            
        is_failure = random.random() < fail_prob
        
        if not is_failure:
            status = "success"
            failure_reason = None
            retry_count = 0
            recovery_status = "none"
            recovery_probability = 0.0
            recommended_action = None
            recovery_attempts = 0
            recovered_amount = 0.0
            priority_score = 0.0
            explainability_notes = None
            customer_stats[c_id]["success"] += 1
        else:
            customer_stats[c_id]["failed"] += 1
            # Pick failure reason
            if method == "UPI":
                failure_reason = random.choices(
                    ["UPI Failure", "Payment Timeout", "Insufficient Funds", "Bank Decline"],
                    weights=[0.45, 0.25, 0.20, 0.10]
                )[0]
            elif "Card" in method:
                failure_reason = random.choices(
                    ["Card Declined", "Authentication Failure", "Insufficient Funds", "Bank Decline"],
                    weights=[0.35, 0.30, 0.20, 0.15]
                )[0]
            else:
                failure_reason = random.choice(FAILURE_REASONS)
                
            retry_count = random.choices([0, 1, 2, 3], weights=[0.55, 0.25, 0.15, 0.05])[0]
            
            # Compute AI Scoring
            prob, rec_action, prio_score, notes = compute_recovery_scoring(
                amount, method, failure_reason, retry_count, success_rate, prev_success
            )
            recovery_probability = prob
            recommended_action = rec_action
            priority_score = prio_score
            explainability_notes = notes
            
            # Realistic split:
            # Older failures (> 14 days ago) might have already been resolved/recovered in past demo history,
            # while recent failures (< 14 days ago) represent the pending unrecovered pool for the live demo!
            days_ago = (now - txn_time).days
            if days_ago > 14 and random.random() < 0.42:
                status = "recovered"
                recovery_status = "recovered"
                recovery_attempts = retry_count + 1
                recovered_amount = float(amount)
                # Seed audit event for historical recovery
                audit_logs.append((
                    (txn_time + timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
                    txn_id,
                    c_id,
                    "PAYMENT_RECOVERED",
                    f"AI workflow executed {rec_action}. Payment of ₹{amount:,.2f} successfully recovered.",
                    float(amount),
                    "RazorRecover AI Engine"
                ))
            elif days_ago > 20 and random.random() < 0.25:
                status = "abandoned"
                recovery_status = "stopped"
                recovery_attempts = 3
                recovered_amount = 0.0
            else:
                status = "failed"
                recovery_status = "pending_analysis"
                recovery_attempts = 0
                recovered_amount = 0.0
                
        records_to_insert.append((
            txn_id,
            c_id,
            c_name,
            c_email,
            txn_time.strftime("%Y-%m-%d %H:%M:%S"),
            float(amount),
            "INR",
            method,
            status,
            failure_reason,
            retry_count,
            prev_success,
            prev_failed,
            success_rate,
            txn_type,
            recovery_status,
            recovery_probability,
            recommended_action,
            recovery_attempts,
            recovered_amount,
            priority_score,
            explainability_notes,
            txn_time.strftime("%Y-%m-%d %H:%M:%S"),
            txn_time.strftime("%Y-%m-%d %H:%M:%S")
        ))
        
    # Batch insert in chunks of 1000
    chunk_size = 1000
    insert_sql = """
        INSERT INTO transactions (
            transaction_id, customer_id, customer_name, customer_email,
            timestamp, amount, currency, payment_method,
            transaction_status, failure_reason, retry_count,
            previous_success_count, previous_failure_count, customer_success_rate,
            transaction_type, recovery_status, recovery_probability,
            recommended_action, recovery_attempts, recovered_amount,
            priority_score, explainability_notes, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    
    for i in range(0, len(records_to_insert), chunk_size):
        chunk = records_to_insert[i:i + chunk_size]
        execute_many(insert_sql, chunk)
        
    # Insert audit logs
    if audit_logs:
        audit_sql = """
            INSERT INTO audit_logs (timestamp, transaction_id, customer_id, event_type, description, recovered_amount, actor)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        for i in range(0, len(audit_logs), chunk_size):
            chunk = audit_logs[i:i + chunk_size]
            execute_many(audit_sql, chunk)
            
    # Update postgres sequences after seeding IDs
    try:
        with get_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE((SELECT MAX(id) FROM users), 1));")
                cur.execute("SELECT setval(pg_get_serial_sequence('recovery_rules', 'id'), COALESCE((SELECT MAX(id) FROM recovery_rules), 1));")
                cur.execute("SELECT setval(pg_get_serial_sequence('transactions', 'id'), COALESCE((SELECT MAX(id) FROM transactions), 1));")
                cur.execute("SELECT setval(pg_get_serial_sequence('audit_logs', 'id'), COALESCE((SELECT MAX(id) FROM audit_logs), 1));")
    except Exception:
        pass

    total_count = query_db("SELECT COUNT(*) as cnt FROM transactions", one=True)["cnt"]
    print(f"Database successfully seeded with {total_count:,} realistic transaction records.")
    return total_count

if __name__ == "__main__":
    from database.db import init_db
    init_db(force_recreate=True)
    seed_database()
