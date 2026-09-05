import random
from datetime import datetime
from database.db import query_db, execute_db, execute_many, get_db
from engine.stopping_rules import load_active_rules, evaluate_stopping_rules

def execute_recovery_workflow(merchant_actor="Merchant Admin"):
    """
    Executes the approved recovery workflow against pending failed transactions in the database.
    Enforces stopping rules, simulates bounded interventions, updates individual transaction records,
    and logs comprehensive audit trail entries.
    """
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Fetch pending failed transactions
    pending_txns = query_db("""
        SELECT * FROM transactions 
        WHERE transaction_status = 'failed' 
          AND recovery_status IN ('pending_analysis', 'eligible', 'retry_failed')
        ORDER BY priority_score DESC
    """)
    
    total_failures_analyzed = len(pending_txns)
    if total_failures_analyzed == 0:
        return {
            "failures_analyzed": 0,
            "recovery_actions_initiated": 0,
            "payments_successfully_recovered": 0,
            "recovered_amount": 0.0,
            "stopped_by_rules_count": 0,
            "message": "No pending failed transactions requiring recovery."
        }
        
    active_rules = load_active_rules()
    
    # Batch audit log initialization
    audit_entries = []
    audit_entries.append((
        now_str,
        "BATCH_APPROVAL",
        "ALL",
        "MERCHANT_APPROVED",
        f"Merchant approved recovery workflow for {total_failures_analyzed} analyzed failed payments.",
        0.0,
        merchant_actor
    ))
    
    actions_initiated = 0
    payments_recovered = 0
    total_recovered_amount = 0.0
    stopped_count = 0
    
    txns_to_update = []
    
    for t in pending_txns:
        txn_id = t["transaction_id"]
        c_id = t["customer_id"]
        amount = float(t["amount"])
        prob = float(t["recovery_probability"] or 0.5)
        action = t["recommended_action"] or "Smart Retry"
        current_retries = int(t.get("retry_count") or 0)
        current_attempts = int(t.get("recovery_attempts") or 0)
        
        # Evaluate stopping rules
        is_eligible, stop_reason, rule_id = evaluate_stopping_rules(t, active_rules)
        
        if not is_eligible:
            stopped_count += 1
            # Mark transaction as stopped
            txns_to_update.append((
                t["transaction_status"], # remains failed or abandoned
                "stopped",
                current_retries,
                current_attempts,
                0.0,
                f"Stopped by rule {rule_id or 'Guardrail'}: {stop_reason}",
                now_str,
                txn_id
            ))
            audit_entries.append((
                now_str,
                txn_id,
                c_id,
                "STOPPING_RULE_APPLIED",
                f"Stopping rule enforced ({rule_id or 'Guardrail'}): {stop_reason}",
                0.0,
                "RazorRecover AI Engine"
            ))
            continue
            
        # If eligible, initiate recovery action
        actions_initiated += 1
        audit_entries.append((
            now_str,
            txn_id,
            c_id,
            "WORKFLOW_EXECUTED",
            f"Executed intervention '{action}' for ₹{amount:,.2f} via optimal payment rail.",
            0.0,
            "RazorRecover AI Engine"
        ))
        
        # Simulate outcome:
        # The calibrated success rate correlates with the AI probability
        # E.g. high probability (e.g. 0.85) succeeds ~88% of the time, medium (0.60) ~62%, etc.
        recovery_roll = random.random()
        # Slight boost from active AI optimization
        effective_prob = min(0.94, prob * 1.05)
        
        is_success = recovery_roll < effective_prob
        
        new_attempts = current_attempts + 1
        new_retries = current_retries + 1
        
        if is_success:
            payments_recovered += 1
            total_recovered_amount += amount
            
            txns_to_update.append((
                "recovered",
                "recovered",
                new_retries,
                new_attempts,
                amount,
                f"Successfully recovered on attempt {new_attempts} via {action}.",
                now_str,
                txn_id
            ))
            
            audit_entries.append((
                now_str,
                txn_id,
                c_id,
                "PAYMENT_RECOVERED",
                f"Payment successful! ₹{amount:,.2f} recovered via {action}.",
                amount,
                "RazorRecover AI Engine"
            ))
        else:
            # Still failed: check if max retry limit reached now
            final_status = "stopped" if new_retries >= 3 else "retry_failed"
            notes = f"Intervention {action} unfulfilled. Next retry scheduled or bounded limit reached."
            
            txns_to_update.append((
                "failed",
                final_status,
                new_retries,
                new_attempts,
                0.0,
                notes,
                now_str,
                txn_id
            ))
            
            if final_status == "stopped":
                audit_entries.append((
                    now_str,
                    txn_id,
                    c_id,
                    "STOPPING_RULE_APPLIED",
                    f"Max retry ceiling reached ({new_retries} attempts). Automated recovery workflow stopped.",
                    0.0,
                    "RazorRecover AI Engine"
                ))
                
    # Update transactions in SQLite batch
    update_sql = """
        UPDATE transactions 
        SET transaction_status = ?,
            recovery_status = ?,
            retry_count = ?,
            recovery_attempts = ?,
            recovered_amount = ?,
            explainability_notes = ?,
            updated_at = ?
        WHERE transaction_id = ?
    """
    execute_many(update_sql, txns_to_update)
    
    # Insert audit logs
    audit_sql = """
        INSERT INTO audit_logs (timestamp, transaction_id, customer_id, event_type, description, recovered_amount, actor)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    execute_many(audit_sql, audit_entries)
    
    return {
        "failures_analyzed": total_failures_analyzed,
        "recovery_actions_initiated": actions_initiated,
        "payments_successfully_recovered": payments_recovered,
        "recovered_amount": round(total_recovered_amount, 2),
        "stopped_by_rules_count": stopped_count,
        "recovery_success_percentage": round((payments_recovered / actions_initiated * 100), 1) if actions_initiated > 0 else 0.0
    }
