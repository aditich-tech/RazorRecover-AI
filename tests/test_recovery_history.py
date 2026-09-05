import unittest
import json
import urllib.request

BASE_URL = "http://127.0.0.1:5000"

class TestRecoveryHistory(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset DB to ensure fresh dataset with RULE-06 active
        try:
            req = urllib.request.Request(f"{BASE_URL}/api/admin/reseed", method="POST")
            urllib.request.urlopen(req)
        except Exception:
            pass

    def request_json(self, path, method="GET", data=None):
        url = f"{BASE_URL}{path}"
        headers = {"Accept": "application/json"}
        payload = None
        if data is not None:
            headers["Content-Type"] = "application/json"
            payload = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_01_recovery_history_endpoint_structure(self):
        status, data = self.request_json("/api/recovery/history")
        self.assertEqual(status, 200)
        self.assertIn("summary", data)
        self.assertIn("history", data)
        self.assertIn("total", data)
        self.assertIn("page", data)
        self.assertIn("total_pages", data)

        # Summary check
        summary = data["summary"]
        self.assertIn("total_actions", summary)
        self.assertIn("recovered", summary)
        self.assertIn("retried", summary)
        self.assertIn("skipped", summary)
        self.assertGreater(summary["total_actions"], 0)

        # Record fields check
        self.assertGreater(len(data["history"]), 0)
        item = data["history"][0]
        required_fields = [
            "transaction_id", "customer_name", "customer_id", "amount",
            "failure_reason", "customer_success_rate", "ai_action",
            "status", "timestamp", "rule_name", "rule_satisfied", "reason"
        ]
        for f in required_fields:
            self.assertIn(f, item, f"Missing field {f} in history item")

        self.assertIn(item["ai_action"], ["Retry", "Resolve", "Skip"])
        self.assertIn(item["status"], ["Recovered", "Retrying", "Skipped", "Failed"])
        self.assertIsInstance(item["rule_satisfied"], bool)

    def test_02_filter_retried(self):
        status, data = self.request_json("/api/recovery/history?filter=retried")
        self.assertEqual(status, 200)
        for item in data["history"]:
            self.assertEqual(item["ai_action"], "Retry")

    def test_03_filter_resolved(self):
        status, data = self.request_json("/api/recovery/history?filter=resolved")
        self.assertEqual(status, 200)
        for item in data["history"]:
            self.assertEqual(item["ai_action"], "Resolve")

    def test_04_filter_skipped(self):
        status, data = self.request_json("/api/recovery/history?filter=skipped")
        self.assertEqual(status, 200)
        for item in data["history"]:
            self.assertEqual(item["ai_action"], "Skip")

    def test_05_filter_recovered(self):
        status, data = self.request_json("/api/recovery/history?filter=recovered")
        self.assertEqual(status, 200)
        for item in data["history"]:
            self.assertEqual(item["status"], "Recovered")

    def test_06_search_filtering(self):
        # Fetch first item to get customer name
        _, initial = self.request_json("/api/recovery/history?limit=1")
        test_name = initial["history"][0]["customer_name"]
        
        status, search_res = self.request_json(f"/api/recovery/history?search={urllib.parse.quote(test_name)}")
        self.assertEqual(status, 200)
        self.assertGreater(search_res["total"], 0)
        for item in search_res["history"]:
            self.assertTrue(
                test_name.lower() in item["customer_name"].lower() or 
                test_name.lower() in item["customer_id"].lower()
            )

    def test_07_trust_customers_dynamic_evaluation(self):
        """
        Verify that toggling the 'Trust Customers' rule dynamically recalculates AI decisions:
        - When active: customers with success rate < 75% are skipped.
        - When inactive: those customers can be retried/resolved.
        """
        # Ensure rule is active first
        rules_status, rules_data = self.request_json("/api/rules")
        trust_rule = next((r for r in rules_data["rules"] if r["rule_id"] == "RULE-06"), None)
        self.assertIsNotNone(trust_rule, "RULE-06 should exist in database")

        if not trust_rule["is_active"]:
            self.request_json("/api/rules/RULE-06/toggle", method="POST")

        # Check with rule active
        _, active_hist = self.request_json("/api/recovery/history")
        active_skipped = active_hist["summary"]["skipped"]

        # Find an item that was skipped due to customer trust rule
        skipped_items = [x for x in active_hist["history"] if x["ai_action"] == "Skip" and x["customer_success_rate"] < 75]
        if skipped_items:
            skipped_item = skipped_items[0]
            self.assertFalse(skipped_item["rule_satisfied"])
            self.assertIn("Trust Customers", skipped_item["rule_name"])
            self.assertIn("does not meet the required threshold", skipped_item["reason"])

        # Toggle rule OFF
        self.request_json("/api/rules/RULE-06/toggle", method="POST")
        _, inactive_hist = self.request_json("/api/recovery/history")
        inactive_skipped = inactive_hist["summary"]["skipped"]

        # Number of skipped transactions should decrease when Trust Rule is deactivated
        self.assertLess(inactive_skipped, active_skipped, "Deactivating Trust Rule should decrease skipped count")

        # Toggle rule back ON
        self.request_json("/api/rules/RULE-06/toggle", method="POST")
        _, restored_hist = self.request_json("/api/recovery/history")
        self.assertEqual(restored_hist["summary"]["skipped"], active_skipped)

if __name__ == "__main__":
    unittest.main()
