import unittest

from scripts.workflow_policy import (
    assess_task,
    classify_reasoning_effort,
    classify_risk,
    delegation_policy,
    retry_allowed,
)


class WorkflowPolicyTests(unittest.TestCase):
    def test_low_medium_high_classification(self):
        self.assertEqual(classify_risk("Update internal documentation"), "LOW")
        self.assertEqual(classify_risk("Add a feature with a schema change"), "MEDIUM")
        self.assertEqual(classify_risk("Change authentication for the public API"), "HIGH")
        self.assertEqual(classify_risk("Unspecified task"), "MEDIUM")

    def test_risk_and_effort_are_separate(self):
        assessment = assess_task("Small security configuration change")
        self.assertEqual(assessment.risk, "HIGH")
        self.assertEqual(assessment.reasoning_effort, "LOW")
        self.assertEqual(classify_reasoning_effort("Ambiguous internal tooling change"), "HIGH")

    def test_delegation_limits_and_stop_conditions(self):
        self.assertEqual(delegation_policy("LOW")["max_sub_agents"], 0)
        self.assertEqual(delegation_policy("MEDIUM")["max_sub_agents"], 1)
        self.assertEqual(delegation_policy("HIGH")["required_gates"], ("GATE-0", "GATE-1", "GATE-2", "GATE-3"))
        self.assertFalse(retry_allowed(2))
        self.assertIn("verification", delegation_policy("LOW")["stop_condition"])


if __name__ == "__main__":
    unittest.main()
