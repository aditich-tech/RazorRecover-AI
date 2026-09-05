import json
from database.db import query_db

def load_active_rules():
    """Loads active rules from the database to enforce dynamically."""
    rules = query_db("SELECT * FROM recovery_rules WHERE is_active = 1")
    return rules or []

def evaluate_stopping_rules(transaction, active_rules=None):
    """
    Evaluates whether a transaction is eligible for recovery or must be stopped.
    Returns:
      (is_eligible: bool, reason: str, applied_rule_id: str or None)
    """
    # 1. Stop if already successful or recovered
    if transaction["transaction_status"] in ["success", "recovered"]:
        return False, "STOP_ALREADY_SUCCESS: Payment has already been settled successfully.", None
        
    # 2. Maximum retry stopping rule (default 3 retries max)
    retry_count = int(transaction.get("retry_count") or 0)
    recovery_attempts = int(transaction.get("recovery_attempts") or 0)
    max_retries = 3
    
    # Check if a custom stopping rule exists in DB
    if active_rules is None:
        active_rules = load_active_rules()
        
    for r in active_rules:
        if r["rule_type"] == "stopping_rule":
            try:
                cond = json.loads(r["condition_json"])
                if "max_retries" in cond:
                    max_retries = int(cond["max_retries"])
            except Exception:
                pass
                
    if retry_count >= max_retries or recovery_attempts >= max_retries:
        return False, f"STOP_MAX_RETRIES: Maximum retry ceiling of {max_retries} attempts reached. Recovery halted to prevent customer fatigue.", "RULE-04"
        
    # 3. Minimum recovery probability stopping rule (default 25% minimum)
    prob = float(transaction.get("recovery_probability") or 0.0)
    min_prob = 0.25
    for r in active_rules:
        if r["rule_type"] == "stopping_rule":
            try:
                cond = json.loads(r["condition_json"])
                if "min_probability" in cond:
                    min_prob = float(cond["min_probability"])
            except Exception:
                pass
                
    if prob < min_prob:
        return False, f"STOP_LOW_PROBABILITY: Calculated probability ({int(prob*100)}%) is below active minimum threshold ({int(min_prob*100)}%). Direct recovery skipped.", "RULE-05"
        
    # 4. Customer Trust stopping rule (e.g. min_customer_success_rate >= 0.75)
    cust_sr = float(transaction.get("customer_success_rate") or 0.0)
    for r in active_rules:
        if r.get("is_active") == 1:
            try:
                cond = json.loads(r.get("condition_json") or "{}")
                if "min_customer_success_rate" in cond:
                    min_sr = float(cond["min_customer_success_rate"])
                    if cust_sr < min_sr:
                        return False, f"STOP_CUSTOMER_TRUST: Customer historical success rate ({int(cust_sr*100)}%) is below required {int(min_sr*100)}% threshold.", r.get("rule_id", "RULE-TRUST")
            except Exception:
                pass
            if r.get("rule_type") == "trust_customers" or "trust" in r.get("rule_name", "").lower():
                if cust_sr < 0.75:
                    return False, f"STOP_CUSTOMER_TRUST: Customer historical success rate ({int(cust_sr*100)}%) is below 75% trust threshold.", r.get("rule_id", "RULE-TRUST")

    # 5. Inactive rule checks
    reason = transaction.get("failure_reason") or ""
    method = transaction.get("payment_method") or ""
    
    smart_retry_active = any(r["rule_type"] == "smart_retry" and r["is_active"] == 1 for r in active_rules)
    upi_rule_active = any(r["rule_type"] == "upi_optimization" and r["is_active"] == 1 for r in active_rules)
    
    if method == "UPI" and not upi_rule_active:
        return False, "STOP_RULE_INACTIVE: UPI optimization rule is currently disabled in merchant settings.", "RULE-02"
        
    if reason in ["Payment Timeout", "Network Error"] and not smart_retry_active:
        return False, "STOP_RULE_INACTIVE: Smart Retry rule is currently inactive.", "RULE-01"
        
    return True, "ELIGIBLE: All stopping rules passed. Transaction approved for recovery workflow execution.", None
