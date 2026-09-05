import urllib.request
import json
import os
import sys

BASE_URL = "http://127.0.0.1:5000"

def make_req(endpoint, method="GET", data=None):
    url = f"{BASE_URL}{endpoint}"
    req_data = json.dumps(data).encode("utf-8") if data is not None else None
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def run_experiment():
    print("=================================================================")
    print("EXPERIMENT: TESTING NEW RECOVERY RULE 'Trust Customers'")
    print("=================================================================")

    # 1. Reset DB to initial clean state
    print("\n[Step 1] Initializing fresh transaction dataset...")
    make_req("/api/admin/reseed", method="POST")

    # 2. Measure metrics BEFORE adding/enabling the 'Trust Customers' rule
    print("\n[Step 2] Collecting BASELINE metrics (BEFORE Trust Customers rule)...")
    stats_before = make_req("/api/dashboard/stats")
    analysis_before = make_req("/api/recovery/analyze")
    
    baseline_pending = stats_before["pending_recoveries"]
    baseline_recoverable = stats_before["potentially_recoverable_revenue"]
    baseline_analysis_rec_count = analysis_before["recommended_for_recovery_count"]
    baseline_analysis_rec_amount = analysis_before["estimated_recoverable_revenue"]

    # Execute recovery on baseline
    exec_before = make_req("/api/recovery/execute", method="POST", data={})
    stats_after_exec_baseline = make_req("/api/dashboard/stats")

    # 3. Reset DB again for fair, identical dataset comparison
    print("\n[Step 3] Resetting dataset to identical state to test WITH 'Trust Customers' rule...")
    make_req("/api/admin/reseed", method="POST")

    # 4. Insert and enable 'Trust Customers' rule
    print("\n[Step 4] Adding new recovery rule: 'Trust Customers' (min_customer_success_rate: 0.75)...")
    rule_payload = {
        "rule_name": "Trust Customers",
        "description": "Retry/resolve a failed payment only when that customer's historical success rate is 75% or higher.",
        "rule_type": "trust_customers",
        "action_type": "SMART_RETRY",
        "condition_json": json.dumps({"min_customer_success_rate": 0.75})
    }
    create_res = make_req("/api/rules", method="POST", data=rule_payload)
    rule_id = create_res["rule_id"]
    print(f"   Created rule {rule_id}: {rule_payload['rule_name']}")

    # 5. Measure metrics AFTER adding 'Trust Customers' rule (prior to execution)
    print("\n[Step 5] Collecting metrics WITH 'Trust Customers' rule...")
    stats_with_rule = make_req("/api/dashboard/stats")
    analysis_with_rule = make_req("/api/recovery/analyze")

    rule_pending = stats_with_rule["pending_recoveries"]
    rule_recoverable = stats_with_rule["potentially_recoverable_revenue"]
    rule_analysis_rec_count = analysis_with_rule["recommended_for_recovery_count"]
    rule_analysis_rec_amount = analysis_with_rule["estimated_recoverable_revenue"]

    # Execute recovery with the rule active
    exec_with_rule = make_req("/api/recovery/execute", method="POST", data={})
    stats_after_exec_rule = make_req("/api/dashboard/stats")

    # 6. Display Comparison Table
    print("\n=================================================================")
    print("METRIC FLUCTUATION COMPARISON: BEFORE VS. AFTER 'TRUST CUSTOMERS'")
    print("=================================================================")
    
    print(f"\n1. PRE-EXECUTION ELIGIBILITY & EXPECTED RECOVERY:")
    print(f"   {'Metric':<35} | {'Before Rule':<18} | {'After Rule':<18} | {'Delta / Impact'}")
    print(f"   {'-'*35}-+-{'-'*18}-+-{'-'*18}-+-{'-'*20}")
    
    delta_pending = rule_pending - baseline_pending
    delta_recoverable = rule_recoverable - baseline_recoverable
    delta_rec_count = rule_analysis_rec_count - baseline_analysis_rec_count
    delta_rec_amt = rule_analysis_rec_amount - baseline_analysis_rec_amount

    print(f"   {'Eligible Pending Recoveries':<35} | {baseline_pending:<18} | {rule_pending:<18} | {delta_pending:+d} ({delta_pending/baseline_pending*100:.1f}%)")
    print(f"   {'Potentially Recoverable Revenue':<35} | INR {baseline_recoverable:,.2f} | INR {rule_recoverable:,.2f} | INR {delta_recoverable:+,.2f} ({delta_recoverable/baseline_recoverable*100:.1f}%)")
    print(f"   {'AI Recommended Txn Count':<35} | {baseline_analysis_rec_count:<18} | {rule_analysis_rec_count:<18} | {delta_rec_count:+d} ({delta_rec_count/baseline_analysis_rec_count*100:.1f}%)")
    print(f"   {'Expected Recovered Revenue':<35} | INR {baseline_analysis_rec_amount:,.2f} | INR {rule_analysis_rec_amount:,.2f} | INR {delta_rec_amt:+,.2f} ({delta_rec_amt/baseline_analysis_rec_amount*100:.1f}%)")

    print(f"\n2. EXECUTION OUTCOME (Simulated Workflow Run):")
    print(f"   {'Execution Metric':<35} | {'Before Rule':<18} | {'After Rule':<18} | {'Delta / Impact'}")
    print(f"   {'-'*35}-+-{'-'*18}-+-{'-'*18}-+-{'-'*20}")

    actions_b = exec_before["recovery_actions_initiated"]
    actions_a = exec_with_rule["recovery_actions_initiated"]
    stopped_b = exec_before["stopped_by_rules_count"]
    stopped_a = exec_with_rule["stopped_by_rules_count"]
    recovered_cnt_b = exec_before["payments_successfully_recovered"]
    recovered_cnt_a = exec_with_rule["payments_successfully_recovered"]
    recovered_amt_b = exec_before["recovered_amount"]
    recovered_amt_a = exec_with_rule["recovered_amount"]
    succ_rate_b = exec_before["recovery_success_percentage"]
    succ_rate_a = exec_with_rule["recovery_success_percentage"]

    print(f"   {'Retry Attempts Initiated':<35} | {actions_b:<18} | {actions_a:<18} | {actions_a - actions_b:+d} attempts")
    print(f"   {'Stopped by Stopping Rules':<35} | {stopped_b:<18} | {stopped_a:<18} | {stopped_a - stopped_b:+d} stopped")
    print(f"   {'Payments Successfully Recovered':<35} | {recovered_cnt_b:<18} | {recovered_cnt_a:<18} | {recovered_cnt_a - recovered_cnt_b:+d} payments")
    print(f"   {'Actual Recovered Revenue':<35} | INR {recovered_amt_b:,.2f} | INR {recovered_amt_a:,.2f} | INR {recovered_amt_a - recovered_amt_b:+,.2f}")
    print(f"   {'Execution Recovery Success Rate':<35} | {succ_rate_b:<18}% | {succ_rate_a:<18}% | {succ_rate_a - succ_rate_b:+.1f}% efficiency lift")

    print(f"\n3. POST-EXECUTION DASHBOARD IMPACT:")
    final_rec_b = stats_after_exec_baseline["revenue_already_recovered"]
    final_rec_a = stats_after_exec_rule["revenue_already_recovered"]
    final_rate_b = stats_after_exec_baseline["recovery_rate"]
    final_rate_a = stats_after_exec_rule["recovery_rate"]
    print(f"   {'Total Revenue Already Recovered':<35} | INR {final_rec_b:,.2f} | INR {final_rec_a:,.2f} | INR {final_rec_a - final_rec_b:+,.2f}")
    print(f"   {'Overall Dashboard Recovery Rate':<35} | {final_rate_b:<18}% | {final_rate_a:<18}% | {final_rate_a - final_rate_b:+.1f}%")

if __name__ == "__main__":
    run_experiment()
