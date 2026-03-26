from __future__ import annotations

import unittest
from pathlib import Path

from agentwork.core.bundles import load_bundles
from agentwork.core.contracts import load_contract
from agentwork.core.validation import validate_bundles, validate_contract, validate_result


class ValidationTest(unittest.TestCase):
    def test_sample_contract_and_bundles_validate(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        contract = load_contract(workspace / "contracts" / "sre-alerts.yaml")
        bundles = load_bundles(workspace / "bundles" / "sre-alerts.yaml")
        validate_contract(contract)
        validate_bundles(bundles)

    def test_invalid_contract_missing_expectations_fails(self) -> None:
        with self.assertRaises(ValueError):
            validate_contract(
                {
                    "id": "bad",
                    "version": "0.1.0",
                    "domain": "sre_ops",
                    "description": "bad contract",
                    "acceptance": {
                        "design": {
                            "min_completion_rate": 0.7,
                            "min_safety_score": 1.0,
                            "min_trials": 5,
                            "confidence": 0.9,
                        }
                    },
                }
            )

    def test_invalid_bundle_requirements_shape_fails(self) -> None:
        with self.assertRaises(ValueError):
            validate_bundles(
                [
                    {
                        "id": "bundle-1",
                        "bundle_type": "sre.alert_triage",
                        "prompt": "prompt",
                        "context": {},
                        "expected": {},
                        "requirements": {
                            "required_tools": "fetch_metrics",
                        },
                    }
                ]
            )

    def test_invalid_result_missing_steps_fails(self) -> None:
        with self.assertRaises(ValueError):
            validate_result(
                {
                    "response": "ok",
                    "structured": {},
                    "tool_calls": [],
                    "usage": {},
                    "latency_ms": 42,
                    "metadata": {},
                }
            )

