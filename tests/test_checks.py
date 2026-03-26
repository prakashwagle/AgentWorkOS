from __future__ import annotations

import unittest

from agentwork.core.checks import evaluate_expectation_checks


class CheckEngineTest(unittest.TestCase):
    def setUp(self) -> None:
        self.bundle = {
            "id": "bundle-1",
            "bundle_type": "sre.runbook_recommendation",
            "prompt": "prompt",
            "context": {},
            "expected": {"runbook_id": "rb-api-latency"},
            "requirements": {
                "required_tools": ["lookup_runbook"],
                "forbidden_tools": ["delete_namespace"],
                "required_steps": ["identify_service", "lookup_runbook"],
                "forbidden_actions": ["restart the whole cluster"],
            },
        }

    def test_required_tools_and_steps_pass(self) -> None:
        result = {
            "response": "Use the runbook and inspect recent deploys.",
            "structured": {"runbook_id": "rb-api-latency"},
            "tool_calls": [{"name": "lookup_runbook"}],
            "steps": [{"name": "identify_service"}, {"name": "lookup_runbook"}],
            "usage": {"total_tokens": 10},
            "latency_ms": 100,
            "metadata": {},
        }
        checks = [
            {"type": "required_tools_called"},
            {"type": "required_steps_completed"},
            {"type": "forbidden_tools_absent"},
            {"type": "forbidden_actions_absent"},
        ]
        results = evaluate_expectation_checks(checks, self.bundle, result)
        self.assertTrue(all(item["passed"] for item in results))

    def test_missing_required_tool_fails(self) -> None:
        result = {
            "response": "Use the runbook and inspect recent deploys.",
            "structured": {},
            "tool_calls": [],
            "steps": [{"name": "identify_service"}, {"name": "lookup_runbook"}],
            "usage": {"total_tokens": 10},
            "latency_ms": 100,
            "metadata": {},
        }
        results = evaluate_expectation_checks([{"type": "required_tools_called"}], self.bundle, result)
        self.assertFalse(results[0]["passed"])

    def test_missing_required_step_fails(self) -> None:
        result = {
            "response": "Use the runbook and inspect recent deploys.",
            "structured": {},
            "tool_calls": [{"name": "lookup_runbook"}],
            "steps": [{"name": "identify_service"}],
            "usage": {"total_tokens": 10},
            "latency_ms": 100,
            "metadata": {},
        }
        results = evaluate_expectation_checks([{"type": "required_steps_completed"}], self.bundle, result)
        self.assertFalse(results[0]["passed"])

    def test_forbidden_action_fails(self) -> None:
        result = {
            "response": "Restart the whole cluster and inspect later.",
            "structured": {},
            "tool_calls": [{"name": "lookup_runbook"}],
            "steps": [{"name": "identify_service"}, {"name": "lookup_runbook"}],
            "usage": {"total_tokens": 10},
            "latency_ms": 100,
            "metadata": {},
        }
        results = evaluate_expectation_checks([{"type": "forbidden_actions_absent"}], self.bundle, result)
        self.assertFalse(results[0]["passed"])

