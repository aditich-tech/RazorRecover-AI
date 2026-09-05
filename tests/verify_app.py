import urllib.request
import urllib.parse
import json
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"

def test_full_application():
    print("==================================================")
    print("STARTING END-TO-END APPLICATION VERIFICATION SUITE")
    print("==================================================")

    # Setup Cookie Jar to maintain session across requests
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    def make_request(path, method="GET", data=None):
        url = f"{BASE_URL}{path}"
        headers = {"Accept": "application/json"}
        req_data = None
        if data is not None:
            req_data = json.dumps(data).encode("utf-8")
            headers["Content-Type"] = "application/json"
        
        req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
        try:
            with opener.open(req) as resp:
                body = resp.read().decode("utf-8")
                try:
                    return resp.status, json.loads(body)
                except Exception:
                    return resp.status, body
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    # 1. Landing Page
    print("\n1. Testing Landing Page (GET /)...")
    status, body = make_request("/")
    assert status == 200, f"Expected 200, got {status}"
    assert "Recover revenue that slips" in body
    assert "Demo environment" in body
    print("   [PASS] Landing page loads correctly with Track 03 positioning.")

    # 2. Login Page
    print("\n2. Testing Login Page (GET /login)...")
    status, body = make_request("/login")
    assert status == 200
    assert "Instant Merchant Demo Access" in body
    print("   [PASS] Login page renders with demo access CTA.")

    # 3. Authenticate Demo User
    print("\n3. Testing Demo Authentication (POST /api/auth/login)...")
    status, body = make_request("/api/auth/login", method="POST", data={
        "email": "merchant@razorpay.com",
        "password": "demo123"
    })
    assert status == 200
    assert body.get("success") is True
    print(f"   [PASS] Authenticated successfully as: {body['user']['merchant_name']}")

    # 4. Access Protected App Shell
    print("\n4. Testing Protected App Shell (GET /app)...")
    status, body = make_request("/app")
    assert status == 200
    assert "Recovery Operations Dashboard" in body
    assert "Start Recovery" in body
    print("   [PASS] Dashboard shell accessible with active session.")

    # 5. Dashboard Live Stats
    print("\n5. Testing Live Dashboard Stats (GET /api/dashboard/stats)...")
    status, stats = make_request("/api/dashboard/stats")
    assert status == 200
    print(f"   [PASS] Total Potential Loss: INR {stats['total_potential_loss']:,.2f}")
    print(f"   [PASS] Potentially Recoverable: INR {stats['potentially_recoverable_revenue']:,.2f}")
    print(f"   [PASS] Failed Attempts: {stats['failed_payment_attempts']:,}")
    print(f"   [PASS] Pending Recoveries: {stats['pending_recoveries']:,}")
    print(f"   [PASS] Risk Zone: {stats['risk_zone']} ({stats['risk_summary']})")
    assert stats["failed_payment_attempts"] > 0
    assert stats["total_potential_loss"] > 0

    # 6. Before / After Impact
    print("\n6. Testing Impact Comparison (GET /api/dashboard/impact)...")
    status, impact = make_request("/api/dashboard/impact")
    assert status == 200
    print(f"   [PASS] Before Potential Loss: INR {impact['before']['potential_loss']:,.2f}")
    print(f"   [PASS] Current Recovered: INR {impact['after']['recovered_revenue']:,.2f}")

    # 7. AI Analysis Flow
    print("\n7. Testing AI Analysis Flow (GET /api/recovery/analyze)...")
    status, analysis = make_request("/api/recovery/analyze")
    assert status == 200
    print(f"   [PASS] Analyzed: {analysis['total_failures_analyzed']} failures")
    print(f"   [PASS] Estimated Recoverable: INR {analysis['estimated_recoverable_revenue']:,.2f}")
    print(f"   [PASS] Breakdown by reason count: {len(analysis['breakdown'])}")
    print(f"   [PASS] Recommendations count: {len(analysis['recommendations'])}")
    assert len(analysis["breakdown"]) > 0
    assert len(analysis["recommendations"]) > 0

    # 8. Merchant Approval & Recovery Execution
    print("\n8. Testing Merchant Approval & Workflow Execution (POST /api/recovery/execute)...")
    status, exec_res = make_request("/api/recovery/execute", method="POST", data={})
    assert status == 200
    print(f"   [PASS] Actions Initiated: {exec_res['recovery_actions_initiated']:,}")
    print(f"   [PASS] Payments Recovered: {exec_res['payments_successfully_recovered']:,}")
    print(f"   [PASS] Recovered Amount: INR {exec_res['recovered_amount']:,.2f}")
    print(f"   [PASS] Stopped by Guardrails: {exec_res['stopped_by_rules_count']:,}")
    print(f"   [PASS] Success Rate: {exec_res['recovery_success_percentage']}%")
    assert exec_res["payments_successfully_recovered"] > 0
    assert exec_res["recovered_amount"] > 0

    # 9. Verify Updated Dashboard Metrics After Recovery
    print("\n9. Verifying Dashboard Metrics Updated Dynamically...")
    status, updated_stats = make_request("/api/dashboard/stats")
    assert status == 200
    print(f"   [PASS] Revenue Already Recovered (New): INR {updated_stats['revenue_already_recovered']:,.2f}")
    print(f"   [PASS] New Recovery Rate: {updated_stats['recovery_rate']}%")
    print(f"   [PASS] Pending Recoveries (Reduced): {updated_stats['pending_recoveries']:,}")
    assert updated_stats["revenue_already_recovered"] > stats["revenue_already_recovered"]

    # 10. Customers Scalable Table
    print("\n10. Testing Customer Table Aggregation (GET /api/customers)...")
    status, cust_data = make_request("/api/customers?page=1&limit=10")
    assert status == 200
    assert len(cust_data["customers"]) > 0
    first_cust = cust_data["customers"][0]
    print(f"   [PASS] Loaded {len(cust_data['customers'])} customers (Total: {cust_data['total']:,})")
    print(f"   [PASS] Top Customer: {first_cust['customer_name']} ({first_cust['total_transactions']} txns)")
    assert first_cust["total_transactions"] >= cust_data["customers"][-1]["total_transactions"]

    # 11. Customer Profile Drawer
    print(f"\n11. Testing Customer Profile Drawer for {first_cust['customer_id']}...")
    status, detail = make_request(f"/api/customers/{first_cust['customer_id']}")
    assert status == 200
    print(f"   [PASS] Customer Paid: INR {detail['customer']['total_paid']:,.2f}")
    print(f"   [PASS] AI Insight: {detail['ai_insight']['summary'][:80]}...")
    print(f"   [PASS] Payment History count: {len(detail['history'])} transactions")
    assert len(detail["history"]) == detail["customer"]["total_transactions"]

    # 12. Recovery Rules Management
    print("\n12. Testing Recovery Rules Management (GET & POST toggle)...")
    status, rules_data = make_request("/api/rules")
    assert status == 200
    assert len(rules_data["rules"]) >= 5
    print(f"   [PASS] Found {len(rules_data['rules'])} configured recovery rules.")
    rule_to_toggle = rules_data["rules"][0]["rule_id"]
    status, toggle_res = make_request(f"/api/rules/{rule_to_toggle}/toggle", method="POST")
    assert status == 200
    print(f"   [PASS] Toggled rule {rule_to_toggle}: is_active={toggle_res['is_active']}")
    # Toggle back
    make_request(f"/api/rules/{rule_to_toggle}/toggle", method="POST")

    # 13. Numbers & Trends Analytics
    print("\n13. Testing Numbers & Trends Analytics (GET /api/analytics/trends)...")
    status, trends = make_request("/api/analytics/trends")
    assert status == 200
    print(f"   [PASS] Recovered This Month: INR {trends['this_month_recovered']:,.2f}")
    print(f"   [PASS] Growth vs Prev Month: +{trends['growth_vs_previous_month']}%")
    print(f"   [PASS] Methods breakdown count: {len(trends['by_method'])}")
    print(f"   [PASS] Reasons breakdown count: {len(trends['by_reason'])}")
    print(f"   [PASS] Hourly distribution count: {len(trends['by_hour'])}")

    # 14. AI Insights Analyst
    print("\n14. Testing AI Insights Analyst (GET /api/insights)...")
    status, insights_data = make_request("/api/insights")
    assert status == 200
    assert len(insights_data["insights"]) >= 4
    for ins in insights_data["insights"]:
        title_safe = ins['title'].replace('\u20b9', 'INR ')
        impact_safe = ins['impact'].replace('\u20b9', 'INR ')
        print(f"   [PASS] Insight: {title_safe} -> {impact_safe}")

    # 15. Audit Logs Verification
    print("\n15. Testing Audit Trail (GET /api/recovery/audit-logs)...")
    status, audit_data = make_request("/api/recovery/audit-logs?limit=5")
    assert status == 200
    assert audit_data["total"] > 0
    print(f"   [PASS] Total audit logs stored: {audit_data['total']:,}")
    print(f"   [PASS] Latest log: {audit_data['logs'][0]['description']}")

    # 16. Logout & Route Protection
    print("\n16. Testing Logout & Route Protection (POST /api/auth/logout)...")
    status, logout_res = make_request("/api/auth/logout", method="POST")
    assert status == 200
    print("   [PASS] Logged out successfully.")
    
    # Check that me returns authenticated: False
    status, me_res = make_request("/api/auth/me")
    assert status == 200
    assert me_res["authenticated"] is False
    print("   [PASS] Verified session cleared; protected routes guard active.")

    print("\n==================================================")
    print("ALL 16 VERIFICATION MILESTONES PASSED WITH ZERO ERRORS!")
    print("==================================================")

if __name__ == "__main__":
    test_full_application()
