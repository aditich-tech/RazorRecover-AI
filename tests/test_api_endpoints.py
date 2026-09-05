import unittest
import json
import urllib.request
import urllib.parse
import http.cookiejar

BASE_URL = "http://127.0.0.1:5000"

class TestApiEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cookie_jar = http.cookiejar.CookieJar()
        cls.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cls.cookie_jar))

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

    def test_01_landing_page(self):
        status, body, _ = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn("RazorRecover", body)

    def test_02_auth_page(self):
        status, body, _ = self.request("/login")
        self.assertEqual(status, 200)
        self.assertIn("Log In", body)

    def test_03_unauthorized_app_redirect(self):
        # Fresh opener with no cookies
        fresh_opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
        req = urllib.request.Request(f"{BASE_URL}/app")
        with fresh_opener.open(req) as resp:
            # Should redirect to /login
            self.assertTrue(resp.url.endswith("/login"))

    def test_04_auth_login_invalid(self):
        status, body, data = self.request("/api/auth/login", method="POST", data={"email": "wrong@example.com", "password": "wrong"})
        self.assertEqual(status, 401)
        self.assertFalse(data.get("success"))

    def test_05_auth_login_demo(self):
        status, body, data = self.request("/api/auth/login", method="POST", data={"email": "merchant@razorpay.com", "password": "demo"})
        self.assertEqual(status, 200)
        self.assertTrue(data.get("success"))
        self.assertEqual(data["user"]["email"], "merchant@razorpay.com")

    def test_06_auth_me(self):
        status, body, data = self.request("/api/auth/me")
        self.assertEqual(status, 200)
        self.assertTrue(data.get("authenticated"))
        self.assertIsNotNone(data.get("user"))

    def test_07_app_page_authenticated(self):
        status, body, _ = self.request("/app")
        self.assertEqual(status, 200)
        self.assertIn("RazorRecover AI", body)

    def test_08_dashboard_stats(self):
        status, body, data = self.request("/api/dashboard/stats")
        self.assertEqual(status, 200)
        self.assertIn("total_potential_loss", data)
        self.assertIn("failed_payment_attempts", data)
        self.assertIn("revenue_already_recovered", data)
        self.assertIn("recovery_rate", data)
        self.assertIn("risk_zone", data)

    def test_09_dashboard_impact(self):
        status, body, data = self.request("/api/dashboard/impact")
        self.assertEqual(status, 200)
        self.assertIn("before", data)
        self.assertIn("after", data)
        self.assertIn("potential_loss", data["before"])
        self.assertIn("recovered_revenue", data["after"])

    def test_10_recovery_analyze(self):
        status, body, data = self.request("/api/recovery/analyze")
        self.assertEqual(status, 200)
        self.assertIn("breakdown", data)
        self.assertIn("recommendations", data)
        self.assertIn("prioritized_queue", data)

    def test_11_audit_logs(self):
        status, body, data = self.request("/api/recovery/audit-logs?page=1&limit=10")
        self.assertEqual(status, 200)
        self.assertIn("logs", data)
        self.assertIn("total", data)
        self.assertIn("total_pages", data)

    def test_12_customers_list_and_search(self):
        status, body, data = self.request("/api/customers?page=1&limit=10")
        self.assertEqual(status, 200)
        self.assertIn("customers", data)
        self.assertGreater(len(data["customers"]), 0)
        cust_id = data["customers"][0]["customer_id"]

        # Search test
        status, body, data_search = self.request(f"/api/customers?search={cust_id}")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(data_search["total"], 1)

    def test_13_customer_detail(self):
        status, body, data = self.request("/api/customers?page=1&limit=1")
        cust_id = data["customers"][0]["customer_id"]
        status, body, detail = self.request(f"/api/customers/{cust_id}")
        self.assertEqual(status, 200)
        self.assertIn("customer", detail)
        self.assertIn("history", detail)
        self.assertIn("ai_insight", detail)

    def test_14_rules_get_and_toggle(self):
        status, body, data = self.request("/api/rules")
        self.assertEqual(status, 200)
        self.assertIn("rules", data)
        self.assertGreater(len(data["rules"]), 0)
        rule_id = data["rules"][0]["rule_id"]
        original_state = data["rules"][0]["is_active"]

        # Toggle rule
        status, body, toggle_data = self.request(f"/api/rules/{rule_id}/toggle", method="POST")
        self.assertEqual(status, 200)
        self.assertTrue(toggle_data.get("success"))
        self.assertNotEqual(toggle_data.get("is_active"), original_state)

        # Toggle back
        status, body, toggle_back = self.request(f"/api/rules/{rule_id}/toggle", method="POST")
        self.assertEqual(status, 200)
        self.assertEqual(toggle_back.get("is_active"), original_state)

    def test_15_analytics_trends(self):
        status, body, data = self.request("/api/analytics/trends")
        self.assertEqual(status, 200)
        self.assertIn("kpis", data)
        self.assertIn("by_method", data)
        self.assertIn("by_reason", data)
        self.assertIn("by_hour", data)
        self.assertIn("trend_data", data)

    def test_16_ai_insights(self):
        status, body, data = self.request("/api/insights")
        self.assertEqual(status, 200)
        self.assertIn("insights", data)
        self.assertGreater(len(data["insights"]), 0)

    def test_17_recovery_history(self):
        status, body, data = self.request("/api/recovery/history?filter=all&page=1&limit=10")
        self.assertEqual(status, 200)
        self.assertIn("summary", data)
        self.assertIn("history", data)
        self.assertIn("total_actions", data["summary"])
        self.assertGreater(len(data["history"]), 0)

if __name__ == "__main__":
    unittest.main()
