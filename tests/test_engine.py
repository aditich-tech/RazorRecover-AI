import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import query_db, execute_db, is_db_seeded
from engine.recovery_engine import analyze_payment_failures, generate_customer_insight
from engine.stopping_rules import evaluate_stopping_rules
from engine.workflow_executor import execute_recovery_workflow

class TestRazorRecoverAI(unittest.TestCase):

    def test_01_database_seeded(self):
        """Verify database contains at least 10,000 realistic records."""
        self.assertTrue(is_db_seeded(), "Database should be seeded with >= 10,000 records.")
        total_txns = query_db("SELECT COUNT(*) as cnt FROM transactions", one=True)["cnt"]
        print(f"\n[PASS] Verified total transaction count in DB: {total_txns:,} records")
        self.assertGreaterEqual(total_txns, 10000)

    def test_02_recovery_analysis(self):
        """Verify AI failure analysis calculates live statistics and breakdowns."""
        # Ensure some pending failures exist even if previous tests ran full recovery
        execute_db("UPDATE transactions SET transaction_status = 'failed', recovery_status = 'pending_analysis' WHERE id IN (SELECT id FROM transactions WHERE failure_reason IS NOT NULL LIMIT 25)")
        analysis = analyze_payment_failures()
        self.assertIn("total_failures_analyzed", analysis)
        self.assertIn("total_potential_loss", analysis)
        self.assertIn("breakdown", analysis)
        self.assertIn("recommendations", analysis)
        self.assertIn("prioritized_queue", analysis)
        print(f"[PASS] Analyzed {analysis['total_failures_analyzed']} failed payments. Potential Loss: INR {analysis['total_potential_loss']:,.2f}")
        self.assertGreater(analysis["total_failures_analyzed"], 0)
        self.assertGreater(len(analysis["breakdown"]), 0)

    def test_03_stopping_rules(self):
        """Verify stopping rules halt excessive retries and low probability payments."""
        # 1. Stopped by max retries
        dummy_high_retries = {
            "transaction_status": "failed",
            "retry_count": 3,
            "recovery_attempts": 3,
            "recovery_probability": 0.85,
            "failure_reason": "Payment Timeout",
            "payment_method": "UPI"
        }
        eligible, reason, rule_id = evaluate_stopping_rules(dummy_high_retries)
        self.assertFalse(eligible)
        self.assertIn("STOP_MAX_RETRIES", reason)
        
        # 2. Stopped by low probability
        dummy_low_prob = {
            "transaction_status": "failed",
            "retry_count": 0,
            "recovery_attempts": 0,
            "recovery_probability": 0.15,
            "failure_reason": "Card Declined",
            "payment_method": "Credit Card"
        }
        eligible, reason, rule_id = evaluate_stopping_rules(dummy_low_prob)
        self.assertFalse(eligible)
        self.assertIn("STOP_LOW_PROBABILITY", reason)

        # 3. Stopped by Trust Customers rule (customer_success_rate < 0.75)
        dummy_low_trust = {
            "transaction_status": "failed",
            "retry_count": 0,
            "recovery_attempts": 0,
            "recovery_probability": 0.85,
            "customer_success_rate": 0.60,
            "failure_reason": "Payment Timeout",
            "payment_method": "UPI"
        }
        active_rules_with_trust = [
            {"rule_id": "RULE-01", "rule_type": "smart_retry", "is_active": 1, "rule_name": "Smart Retry"},
            {"rule_id": "RULE-02", "rule_type": "upi_optimization", "is_active": 1, "rule_name": "UPI Optimization"},
            {"rule_id": "RULE-TRUST", "rule_name": "Trust Customers", "rule_type": "trust_customers", "condition_json": '{"min_customer_success_rate": 0.75}', "is_active": 1}
        ]
        eligible, reason, rule_id = evaluate_stopping_rules(dummy_low_trust, active_rules_with_trust)
        self.assertFalse(eligible)
        self.assertIn("STOP_CUSTOMER_TRUST", reason)

        # 4. Eligible transaction
        dummy_eligible = {
            "transaction_status": "failed",
            "retry_count": 0,
            "recovery_attempts": 0,
            "recovery_probability": 0.82,
            "customer_success_rate": 0.88,
            "failure_reason": "Payment Timeout",
            "payment_method": "UPI"
        }
        eligible, reason, rule_id = evaluate_stopping_rules(dummy_eligible, active_rules_with_trust)
        self.assertTrue(eligible)
        print("[PASS] Verified stopping rules correctly block high retries, low probability, and low customer trust while permitting eligible cases.")

    def test_04_customer_aggregation(self):
        """Verify customer table aggregations group transactions correctly and sort by volume."""
        custs = query_db("""
            SELECT customer_id, customer_name, COUNT(*) as total_transactions
            FROM transactions
            GROUP BY customer_id, customer_name
            ORDER BY total_transactions DESC
            LIMIT 5
        """)
        self.assertGreater(len(custs), 0)
        top_cust = custs[0]
        self.assertGreaterEqual(top_cust["total_transactions"], 1)
        print(f"[PASS] Top customer by volume: {top_cust['customer_name']} ({top_cust['total_transactions']} transactions)")

    def test_05_customer_insight_generation(self):
        """Verify customer profile insight generator generates tailored insights."""
        sample_cust = query_db("SELECT customer_id FROM transactions LIMIT 1", one=True)
        insight = generate_customer_insight(sample_cust["customer_id"])
        self.assertIn("summary", insight)
        self.assertIn("recovery_recommendation", insight)
        self.assertIn("recovery_probability_tier", insight)
        print(f"[PASS] Generated AI insight for {sample_cust['customer_id']}: {insight['summary'][:80]}...")

if __name__ == "__main__":
    unittest.main()
