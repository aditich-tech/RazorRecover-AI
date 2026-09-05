import json
from database.db import query_db
from engine.stopping_rules import load_active_rules

def evaluate_transaction_decision(t, active_rules):
    """
    Dynamically evaluates a transaction against current active rules to determine:
    - AI Action: Retry | Resolve | Skip
    - Status: Recovered | Retrying | Skipped | Failed
    - Customer Success Rate (percent)
    - Active Rule Evaluated
    - Whether the rule was satisfied (bool)
    - Explainable Decision Reason
    """
    # Customer success rate
    cust_sr = float(t.get("customer_success_rate") or 0.0)
    # If 0, fallback to previous_success / (previous_success + previous_failure) if available
    if cust_sr == 0.0:
        succ = int(t.get("previous_success_count") or 0)
        fail = int(t.get("previous_failure_count") or 0)
        if succ + fail > 0:
            cust_sr = succ / (succ + fail)
        else:
            cust_sr = 0.50
    sr_percent = int(round(cust_sr * 100))

    txn_status = t.get("transaction_status") or "failed"
    retry_count = int(t.get("retry_count") or 0)
    recovery_attempts = int(t.get("recovery_attempts") or 0)
    prob = float(t.get("recovery_probability") or 0.5)

    # 1. Check for Trust Customers rule in active rules
    trust_rule = None
    min_trust_sr = 0.75
    for r in active_rules:
        if r.get("is_active") == 1:
            if r.get("rule_type") == "trust_customers" or "trust" in r.get("rule_name", "").lower():
                trust_rule = r
                try:
                    cond = json.loads(r.get("condition_json") or "{}")
                    if "min_customer_success_rate" in cond:
                        min_trust_sr = float(cond["min_customer_success_rate"])
                except Exception:
                    min_trust_sr = 0.75
                break

    # If Trust Customers rule is active:
    if trust_rule:
        threshold_pct = int(min_trust_sr * 100)
        rule_label = f"{trust_rule.get('rule_name', 'Trust Customers')} — minimum {threshold_pct}% success rate"
        
        if cust_sr < min_trust_sr:
            # Does not meet trust threshold -> Skip
            return {
                "ai_action": "Skip",
                "status": "Skipped",
                "customer_success_rate_percent": sr_percent,
                "rule_name": rule_label,
                "rule_satisfied": False,
                "reason": f"Customer does not meet the required threshold ({sr_percent}% < {threshold_pct}%)."
            }
        else:
            # Meets trust threshold -> Can be Retried or Resolved
            if txn_status == "recovered":
                return {
                    "ai_action": "Resolve",
                    "status": "Recovered",
                    "customer_success_rate_percent": sr_percent,
                    "rule_name": rule_label,
                    "rule_satisfied": True,
                    "reason": f"Customer meets the required success-rate threshold ({sr_percent}% >= {threshold_pct}%). Transaction resolved."
                }
            else:
                # Check other stopping boundaries like max retries
                if retry_count >= 3 or recovery_attempts >= 3:
                    return {
                        "ai_action": "Skip",
                        "status": "Skipped",
                        "customer_success_rate_percent": sr_percent,
                        "rule_name": "Max Retry Cap (Stopping Rule)",
                        "rule_satisfied": False,
                        "reason": f"Max retry ceiling of 3 attempts reached. Recovery halted to prevent customer fatigue."
                    }
                return {
                    "ai_action": "Retry",
                    "status": "Retrying",
                    "customer_success_rate_percent": sr_percent,
                    "rule_name": rule_label,
                    "rule_satisfied": True,
                    "reason": f"Customer meets the required success-rate threshold ({sr_percent}% >= {threshold_pct}%)."
                }

    # 2. If Trust Customers rule is not active, evaluate other active stopping rules:
    max_retries = 3
    min_prob = 0.25
    for r in active_rules:
        if r.get("rule_type") == "stopping_rule":
            try:
                cond = json.loads(r.get("condition_json") or "{}")
                if "max_retries" in cond:
                    max_retries = int(cond["max_retries"])
                if "min_probability" in cond:
                    min_prob = float(cond["min_probability"])
            except Exception:
                pass

    if retry_count >= max_retries or recovery_attempts >= max_retries:
        return {
            "ai_action": "Skip",
            "status": "Skipped",
            "customer_success_rate_percent": sr_percent,
            "rule_name": f"Max Retry Cap — maximum {max_retries} attempts",
            "rule_satisfied": False,
            "reason": f"Maximum retry ceiling of {max_retries} attempts reached. Automated recovery skipped."
        }

    if prob < min_prob:
        return {
            "ai_action": "Skip",
            "status": "Skipped",
            "customer_success_rate_percent": sr_percent,
            "rule_name": f"Low Probability Threshold — minimum {int(min_prob*100)}%",
            "rule_satisfied": False,
            "reason": f"Calculated recovery probability ({int(prob*100)}%) is below active threshold ({int(min_prob*100)}%)."
        }

    if txn_status == "recovered":
        return {
            "ai_action": "Resolve",
            "status": "Recovered",
            "customer_success_rate_percent": sr_percent,
            "rule_name": "Smart Retry Engine",
            "rule_satisfied": True,
            "reason": "Payment successfully recovered after automated recovery intervention."
        }

    return {
        "ai_action": "Retry",
        "status": "Retrying",
        "customer_success_rate_percent": sr_percent,
        "rule_name": "Smart Retry Engine",
        "rule_satisfied": True,
        "reason": f"Customer historical reliability ({sr_percent}%) qualifies for automated retry."
    }

def get_recovery_history(filter_type="all", search="", page=1, limit=15):
    """
    Returns dynamically evaluated transaction history with summary KPI counts.
    """
    active_rules = load_active_rules()

    # Query failed and recovered transactions
    query = """
        SELECT 
            transaction_id,
            customer_id,
            customer_name,
            customer_email,
            timestamp,
            amount,
            currency,
            payment_method,
            transaction_status,
            failure_reason,
            retry_count,
            recovery_attempts,
            previous_success_count,
            previous_failure_count,
            customer_success_rate,
            recovery_status,
            recovery_probability,
            recommended_action,
            explainability_notes
        FROM transactions
        WHERE transaction_status IN ('failed', 'recovered', 'abandoned')
           OR recovery_status != 'none'
        ORDER BY timestamp DESC
    """
    rows = query_db(query) or []

    # Dynamically evaluate all transactions against active rules
    evaluated_all = []
    for r in rows:
        decision = evaluate_transaction_decision(r, active_rules)
        item = {
            "transaction_id": r["transaction_id"],
            "customer_id": r["customer_id"],
            "customer_name": r["customer_name"],
            "customer_email": r["customer_email"],
            "amount": float(r["amount"]),
            "failure_reason": r["failure_reason"] or "Payment Error",
            "payment_method": r["payment_method"],
            "timestamp": r["timestamp"],
            "customer_success_rate": decision["customer_success_rate_percent"],
            "ai_action": decision["ai_action"],
            "status": decision["status"],
            "rule_name": decision["rule_name"],
            "rule_satisfied": decision["rule_satisfied"],
            "reason": decision["reason"]
        }
        evaluated_all.append(item)

    # Calculate overall summary counts across all evaluated records
    total_actions = len(evaluated_all)
    count_recovered = sum(1 for x in evaluated_all if x["status"] == "Recovered")
    count_retried = sum(1 for x in evaluated_all if x["ai_action"] == "Retry")
    count_skipped = sum(1 for x in evaluated_all if x["ai_action"] == "Skip")

    summary = {
        "total_actions": total_actions,
        "recovered": count_recovered,
        "retried": count_retried,
        "skipped": count_skipped
    }

    # Filter by filter_type if specified
    filtered = evaluated_all
    filter_norm = (filter_type or "all").strip().lower()
    if filter_norm == "retried":
        filtered = [x for x in filtered if x["ai_action"] == "Retry"]
    elif filter_norm == "resolved":
        filtered = [x for x in filtered if x["ai_action"] == "Resolve"]
    elif filter_norm == "skipped":
        filtered = [x for x in filtered if x["ai_action"] == "Skip"]
    elif filter_norm == "recovered":
        filtered = [x for x in filtered if x["status"] == "Recovered"]

    # Filter by search string
    if search:
        s = search.strip().lower()
        filtered = [
            x for x in filtered 
            if s in x["transaction_id"].lower() 
            or s in x["customer_name"].lower() 
            or s in x["customer_id"].lower()
            or s in x["failure_reason"].lower()
        ]

    total_filtered = len(filtered)
    total_pages = max(1, (total_filtered + limit - 1) // limit) if limit > 0 else 1
    offset = (page - 1) * limit
    paged_items = filtered[offset:offset + limit]

    return {
        "summary": summary,
        "history": paged_items,
        "total": total_filtered,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "active_rules_count": len(active_rules)
    }
