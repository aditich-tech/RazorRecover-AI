import unittest
import json
import re
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"

class TestFullWebsiteSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cookie_jar = http.cookiejar.CookieJar()
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.cookie_jar))

    @classmethod
    def tearDownClass(cls):
        # Reset database to fresh demonstration state
        try:
            req = urllib.request.Request(f"{BASE_URL}/api/admin/reseed", method="POST")
            urllib.request.urlopen(req)
        except Exception:
            pass

    def request(self, path, method="GET", data=None):
        url = f"{BASE_URL}{path}"
        headers = {}
        payload = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with self.opener.open(req) as resp:
                status = resp.status
                body = resp.read().decode("utf-8")
                try:
                    json_data = json.loads(body)
                except Exception:
                    json_data = None
                return status, body, json_data
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8")
            try:
                json_data = json.loads(body)
            except Exception:
                json_data = None
            return e.code, body, json_data

    def test_01_static_assets_referenced_in_templates(self):
        """Verify all JS and CSS resources referenced across all pages resolve with HTTP 200"""
        pages = ["/", "/login"]
        asset_urls = set()
        for page in pages:
            status, body, _ = self.request(page)
            self.assertEqual(status, 200)
            # Find all href="/static/..." and src="/static/..."
            matches = re.findall(r'(?:href|src)=["\'](/static/[^"\']+)["\']', body)
            for m in matches:
                asset_urls.add(m)
        
        # Also check /app assets
        # Authenticate first
        self.request("/api/auth/login", method="POST", data={"email": "merchant@razorpay.com", "password": "demo"})
        status, body, _ = self.request("/app")
        self.assertEqual(status, 200)
        app_matches = re.findall(r'(?:href|src)=["\'](/static/[^"\']+)["\']', body)
        for m in app_matches:
            asset_urls.add(m)

        self.assertGreater(len(asset_urls), 5, "Should have found multiple static asset references")
        for asset in asset_urls:
            status, asset_body, _ = self.request(asset)
            self.assertEqual(status, 200, f"Failed to load asset: {asset}")
            self.assertGreater(len(asset_body), 0, f"Asset is empty: {asset}")

    def test_02_dashboard_and_impact_metrics_consistency(self):
        """Verify dashboard stats and impact stats are mathematically consistent"""
        status, _, stats = self.request("/api/dashboard/stats")
        self.assertEqual(status, 200)
        status, _, impact = self.request("/api/dashboard/impact")
        self.assertEqual(status, 200)

        # Revenue recovered in dashboard should match impact 'after.recovered_revenue'
        self.assertEqual(round(stats["revenue_already_recovered"], 1), round(impact["after"]["recovered_revenue"], 1))
        self.assertEqual(round(stats["total_potential_loss"], 1), round(impact["after"]["remaining_potential_loss"], 1))

    def test_03_ai_recovery_workflow_execution(self):
        """Verify AI recovery execution processes eligible transactions, logs audit trail, and returns execution summary"""
        # First analyze
        status, _, analysis = self.request("/api/recovery/analyze")
        self.assertEqual(status, 200)
        initial_recommended = analysis["recommended_for_recovery_count"]

        # Execute recovery workflow
        status, _, result = self.request("/api/recovery/execute", method="POST")
        self.assertEqual(status, 200)
        self.assertTrue(result.get("success"))
        self.assertIn("payments_successfully_recovered", result)
        self.assertIn("recovered_amount", result)
        self.assertIn("stopped_by_rules_count", result)

        # Verify audit logs received the execution event
        status, _, logs = self.request("/api/recovery/audit-logs?limit=5")
        self.assertEqual(status, 200)
        self.assertGreater(len(logs["logs"]), 0)

    def test_04_customer_pagination_and_sorting(self):
        """Verify customer table pagination and sorting across multiple dimensions"""
        sort_fields = ["total_transactions", "amount", "successful", "failed", "recovered"]
        for field in sort_fields:
            status, _, data = self.request(f"/api/customers?sort={field}&order=DESC&limit=5")
            self.assertEqual(status, 200)
            self.assertIn("customers", data)
            self.assertLessEqual(len(data["customers"]), 5)

    def test_05_customer_deep_profile_and_ai_insight(self):
        """Verify customer deep profile endpoint produces complete breakdown and structured AI insight"""
        status, _, data = self.request("/api/customers?limit=1")
        self.assertEqual(status, 200)
        cust_id = data["customers"][0]["customer_id"]

        status, _, detail = self.request(f"/api/customers/{cust_id}")
        self.assertEqual(status, 200)
        self.assertEqual(detail["customer"]["customer_id"], cust_id)
        self.assertIn("ai_insight", detail)
        self.assertIn("recovery_recommendation", detail["ai_insight"])
        self.assertIn("summary", detail["ai_insight"])
        self.assertIn("recovery_probability_tier", detail["ai_insight"])
        self.assertGreater(len(detail["history"]), 0)

    def test_06_stopping_rules_crud_and_safety(self):
        """Verify stopping rules retrieval, custom rule creation, and toggles"""
        status, _, initial_rules = self.request("/api/rules")
        self.assertEqual(status, 200)
        initial_count = len(initial_rules["rules"])

        # Create a custom rule
        new_rule_payload = {
            "rule_name": "Test High Value Safety Net",
            "description": "Halt automatic recovery retries on transactions exceeding INR 100,000",
            "rule_type": "amount_threshold",
            "action_type": "FLAG_FOR_MANUAL_REVIEW",
            "condition_json": json.dumps({"max_amount": 100000})
        }
        status, _, created = self.request("/api/rules", method="POST", data=new_rule_payload)
        self.assertEqual(status, 200)
        self.assertTrue(created.get("success"))
        created_id = created["rule_id"]

        # Check list again
        status, _, updated_rules = self.request("/api/rules")
        self.assertEqual(len(updated_rules["rules"]), initial_count + 1)

        # Toggle the newly created rule
        status, _, toggle_res = self.request(f"/api/rules/{created_id}/toggle", method="POST")
        self.assertEqual(status, 200)
        self.assertEqual(toggle_res["is_active"], 0)

    def test_07_analytics_trends_structure(self):
        """Verify analytics numbers and trend calculations"""
        status, _, data = self.request("/api/analytics/trends")
        self.assertEqual(status, 200)
        self.assertIn("this_month_recovered", data)
        self.assertIn("growth_vs_previous_month", data)
        self.assertIn("by_method", data)
        self.assertIn("by_reason", data)
        self.assertIn("by_hour", data)
        self.assertIn("trend_data", data)
        self.assertGreater(len(data["by_method"]), 0)
        self.assertGreater(len(data["by_reason"]), 0)
        self.assertGreater(len(data["by_hour"]), 0)

    def test_08_ai_insights_recommendations(self):
        """Verify dynamic AI insights engine produces high-impact merchant recommendations"""
        status, _, data = self.request("/api/insights")
        self.assertEqual(status, 200)
        insights = data.get("insights", [])
        self.assertGreaterEqual(len(insights), 4)
        for item in insights:
            self.assertIn("id", item)
            self.assertIn("title", item)
            self.assertIn("description", item)
            self.assertIn("impact", item)
            self.assertIn("recommended_action", item)

if __name__ == "__main__":
    unittest.main()
