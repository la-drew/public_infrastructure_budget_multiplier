import unittest

from public_infrastructure_budget_multiplier.model import ModelInputError, estimate_project


class EstimateProjectTests(unittest.TestCase):
    def setUp(self):
        self.project = {
            "name": "Test corridor",
            "project_type": "road",
            "phase": "planning",
            "capital_cost": 200,
            "duration_months": 48,
            "simulations": 2000,
        }

    def test_result_is_deterministic(self):
        first = estimate_project(self.project)
        second = estimate_project(self.project)
        self.assertEqual(first, second)

    def test_percentiles_are_ordered(self):
        result = estimate_project(self.project)
        costs = [result["cost"][key]["amount"] for key in ("p10", "p50", "p80", "p90")]
        times = [result["schedule"][key]["months"] for key in ("p10", "p50", "p80", "p90")]
        self.assertEqual(costs, sorted(costs))
        self.assertEqual(times, sorted(times))

    def test_contingency_changes_budget_risk_not_outturn(self):
        low = estimate_project({**self.project, "contingency_percent": 0})
        high = estimate_project({**self.project, "contingency_percent": 50})
        self.assertEqual(low["cost"], high["cost"])
        self.assertGreater(low["probability_exceeding_funded_budget_percent"], high["probability_exceeding_funded_budget_percent"])

    def test_mature_design_reduces_p80(self):
        early = estimate_project({**self.project, "design_completion_percent": 5})
        mature = estimate_project({**self.project, "design_completion_percent": 90})
        self.assertGreater(early["cost"]["p80"]["amount"], mature["cost"]["p80"]["amount"])

    def test_more_approval_complexity_increases_schedule(self):
        routine = estimate_project({**self.project, "approval_complexity": 1})
        exceptional = estimate_project({**self.project, "approval_complexity": 5})
        self.assertGreater(exceptional["schedule"]["p80"]["months"], routine["schedule"]["p80"]["months"])

    def test_rejects_invalid_inputs(self):
        with self.assertRaises(ModelInputError):
            estimate_project({**self.project, "capital_cost": -1})
        with self.assertRaises(ModelInputError):
            estimate_project({**self.project, "project_type": "spaceship"})
        with self.assertRaises(ModelInputError):
            estimate_project([])

    def test_response_contains_reproducibility_metadata(self):
        result = estimate_project(self.project)
        self.assertEqual(result["model_version"], "0.1.0")
        self.assertIsInstance(result["seed"], int)
        self.assertGreaterEqual(len(result["drivers"]), 5)


if __name__ == "__main__":
    unittest.main()

