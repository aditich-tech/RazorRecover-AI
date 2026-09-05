import json
from database.db import query_db
from engine.stopping_rules import evaluate_stopping_rules, load_active_rules

def compute_transaction_score_and_reasons(row):
    """
    Computes explainable recovery probability, priority score, and reasons for a transaction.
    """
    amount = float(row["amount"])
    method = row["payment_method"]
    reason = row.get("failure_reason") or "Unknown"
    retry_count = int(row.get("retry_count") or 0)
    success_rate = float(row.get("customer_success_rate") or 0.75)
    prev_success = int(row.get("previous_success_count") or 0)
    prev_failure = int(row.get("previous_failure_count") or 0)
    
    score = 0.50
    reasons = []
    
    # 1. Failure reason
    if reason in ["Payment Timeout", "Network Error"]:
        score += 0.28
        reasons.append(f"{reason} is an idempotent gateway timeout with ~88% automated retry recovery")
    elif reason == "UPI Failure":
        score += 0.22
        reasons.append("UPI handles high transient PSP spikes; recovery rate jumps upon off-peak query")
    elif reason == "Bank Decline":
        score += 0.05
        reasons.append("Bank issuer decline can be routed via secondary acquiring rail")
    elif reason == "Insufficient Funds":
        score -= 0.16
        reasons.append("Account balance limitation requires scheduled WhatsApp/SMS payment reminder")
    elif reason in ["Card Declined", "Authentication Failure"]:
        score -= 0.10
        reasons.append("Customer 3DS authentication dropped; retry with link or alternate route")
        
    # 2. Customer history
    if success_rate >= 0.80 and prev_success >= 5:
        score += 0.18
        reasons.append(f"High-loyalty customer ({prev_success} successful orders, {int(success_rate*100)}% historical success)")
    elif success_rate >= 0.55:
        score += 0.08
        reasons.append(f"Customer has solid payment history ({prev_success} previous successful payments)")
    elif prev_failure >= 3 and success_rate < 0.35:
        score -= 0.14
        reasons.append(f"High risk profile ({prev_failure} previous failed payments, {int(success_rate*100)}% success)")
        
    # 3. Retry decay
    if retry_count == 0:
        score += 0.10
        reasons.append("First payment attempt: optimum window for immediate Smart Retry")
    elif retry_count == 1:
        score += 0.05
        reasons.append("Second attempt statistically recovers 64% of recoverable payments")
    elif retry_count >= 2:
        score -= 0.20
        reasons.append(f"Prior {retry_count} retries failed; approaching stopping rule boundary")
        
    prob = round(max(0.08, min(0.96, score)), 2)
    
    # Classification
    if prob >= 0.75:
        category = "High"
    elif prob >= 0.40:
        category = "Medium"
    else:
        category = "Low"
        
    # Action recommendation
    if prob >= 0.75:
        if retry_count <= 1 and reason in ["Payment Timeout", "Network Error", "UPI Failure"]:
            action = "Smart Retry"
        else:
            action = "Intelligent Retry Timing"
    elif prob >= 0.45:
        if reason == "Insufficient Funds":
            action = "Payment Reminder"
        elif reason in ["Bank Decline", "Card Declined"]:
            action = "Alternate Payment Route"
        else:
            action = "Intelligent Retry Timing"
    else:
        action = "Alternate Payment Route" if reason in ["Bank Decline", "Card Declined"] else "Payment Reminder"
        
    # Priority Score calculation: balances probability, amount impact, and retry feasibility
    amount_factor = min(2.0, max(0.6, (amount / 3000.0) ** 0.5))
    priority = round(prob * amount_factor * 100, 1)
    
    return {
        "recovery_probability": prob,
        "probability_percent": int(prob * 100),
        "category": category,
        "recommended_action": action,
        "priority_score": priority,
        "reasons": reasons[:3]
    }

def analyze_payment_failures():
    """
    Live query of the dataset to analyze all pending/unrecovered failed transactions.
    Calculates exact real-time failure breakdowns, action recommendations, and priority queue.
    """
    # Query all failed transactions that have not yet been recovered
    failed_txns = query_db("""
        SELECT * FROM transactions 
        WHERE transaction_status = 'failed' 
          AND recovery_status IN ('pending_analysis', 'eligible', 'retry_failed')
        ORDER BY priority_score DESC, amount DESC
    """)
    
    total_failures = len(failed_txns)
    total_potential_loss = sum(float(t["amount"]) for t in failed_txns) if failed_txns else 0.0
    
    # Failure breakdown aggregation
    breakdown_dict = {}
    actions_dict = {
        "Smart Retry": {"count": 0, "amount": 0.0, "description": "Auto-retry high-probability transient failures via optimal gateway"},
        "Intelligent Retry Timing": {"count": 0, "amount": 0.0, "description": "Schedule retries during peak bank processing & customer activity windows"},
        "Payment Reminder": {"count": 0, "amount": 0.0, "description": "Send smart SMS & WhatsApp links with 1-click retry payment sheet"},
        "Alternate Payment Route": {"count": 0, "amount": 0.0, "description": "Switch acquiring bank rail or prompt secondary UPI / Card method"}
    }
    
    high_count, med_count, low_count = 0, 0, 0
    estimated_recoverable_revenue = 0.0
    recommended_for_recovery_count = 0
    
    prioritized_queue = []
    active_rules = load_active_rules()
    
    for t in failed_txns:
        amount = float(t["amount"])
        reason = t["failure_reason"] or "Other"
        
        # Breakdown by reason
        if reason not in breakdown_dict:
            breakdown_dict[reason] = {"reason": reason, "attempts": 0, "potential_loss": 0.0}
        breakdown_dict[reason]["attempts"] += 1
        breakdown_dict[reason]["potential_loss"] += amount
        
        # Re-verify scoring & action
        score_data = compute_transaction_score_and_reasons(t)
        prob = score_data["recovery_probability"]
        action = score_data["recommended_action"]
        cat = score_data["category"]
        
        if cat == "High":
            high_count += 1
        elif cat == "Medium":
            med_count += 1
        else:
            low_count += 1
            
        # Evaluate against active stopping rules dynamically (including Trust Customers)
        is_eligible, _, _ = evaluate_stopping_rules(t, active_rules)
        if is_eligible:
            recommended_for_recovery_count += 1
            # Expected recoverable value = probability * amount * 0.88 (conservative discount)
            estimated_recoverable_revenue += (prob * amount * 0.88)
            
            if action in actions_dict:
                actions_dict[action]["count"] += 1
                actions_dict[action]["amount"] += amount

                
        if len(prioritized_queue) < 15:
            prioritized_queue.append({
                "transaction_id": t["transaction_id"],
                "customer_id": t["customer_id"],
                "customer_name": t["customer_name"],
                "amount": amount,
                "payment_method": t["payment_method"],
                "failure_reason": reason,
                "recovery_probability": prob,
                "probability_percent": int(prob * 100),
                "category": cat,
                "recommended_action": action,
                "priority_score": score_data["priority_score"],
                "reasons": score_data["reasons"]
            })
            
    # Format breakdown list sorted by potential loss
    breakdown_list = sorted(breakdown_dict.values(), key=lambda x: x["potential_loss"], reverse=True)
    
    # Format recommendations list
    recommendations_list = [
        {
            "action": action_name,
            "count": data["count"],
            "amount": round(data["amount"], 2),
            "description": data["description"]
        }
        for action_name, data in actions_dict.items() if data["count"] > 0
    ]
    
    return {
        "total_failures_analyzed": total_failures,
        "total_potential_loss": round(total_potential_loss, 2),
        "estimated_recoverable_revenue": round(estimated_recoverable_revenue, 2),
        "recommended_for_recovery_count": recommended_for_recovery_count,
        "category_counts": {
            "high": high_count,
            "medium": med_count,
            "low": low_count
        },
        "breakdown": breakdown_list,
        "recommendations": recommendations_list,
        "prioritized_queue": prioritized_queue
    }

def generate_customer_insight(customer_id, history=None):
    """
    Generates a personalized AI Insight from the customer's actual transaction history.
    Reuses history if provided to avoid duplicate queries.
    """
    if history is None:
        history = query_db("""
            SELECT * FROM transactions 
            WHERE customer_id = ? 
            ORDER BY timestamp DESC
        """, (customer_id,))
    
    if not history:
        return {
            "summary": "New customer with no prior transaction history.",
            "recovery_recommendation": "Use standard recovery flow.",
            "historical_recovery_rate": 0.0,
            "recovery_probability_tier": "Medium"
        }
        
    total_txns = len(history)
    successes = [t for t in history if t["transaction_status"] in ["success", "recovered"]]
    failures = [t for t in history if t["transaction_status"] in ["failed", "abandoned", "recovered"]]
    recovered_txns = [t for t in history if t["transaction_status"] == "recovered"]
    
    success_rate = (len(successes) / total_txns) if total_txns > 0 else 0
    recovery_rate = (len(recovered_txns) / len(failures)) if failures else 1.0
    
    # Analyze retry patterns
    second_retry_success = 0
    total_retried_failures = 0
    upi_count = 0
    card_count = 0
    
    for t in history:
        if t["payment_method"] == "UPI":
            upi_count += 1
        elif "Card" in t["payment_method"]:
            card_count += 1
        if t["transaction_status"] == "recovered" and (t["retry_count"] or 0) in [1, 2]:
            second_retry_success += 1
        if (t["retry_count"] or 0) > 0:
            total_retried_failures += 1
            
    # Generate tailored narrative
    insights = []
    if len(recovered_txns) >= 2:
        insights.append(f"This customer successfully completed payment after retry in {len(recovered_txns)} of their past failed-payment cases.")
    elif success_rate >= 0.80:
        insights.append(f"High lifetime reliability: {int(success_rate * 100)}% of attempted payments succeed without friction.")
        
    if second_retry_success >= 1:
        insights.append("Second retry historically performs exceptionally well for this user profile.")
        
    fav_method = "UPI" if upi_count > card_count else "Card / Net Banking"
    insights.append(f"Primary preferred payment mechanism is {fav_method}.")
    
    if recovery_rate >= 0.60:
        prob_tier = "High"
        rec = "Prioritize instant Smart Retry. User responds rapidly to automated recovery."
    elif recovery_rate >= 0.30:
        prob_tier = "Medium"
        rec = "Trigger Payment Reminder via WhatsApp/SMS before attempting second retry."
    else:
        prob_tier = "Low"
        rec = "Recommend alternate payment route switch or manual customer outreach."
        
    return {
        "summary": " · ".join(insights) if insights else "Consistent merchant customer with normal payment behavioral distribution.",
        "recovery_recommendation": rec,
        "historical_recovery_rate": round(recovery_rate * 100, 1),
        "recovery_probability_tier": prob_tier
    }
