from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentwork.core.bundles import load_bundles
from agentwork.core.contracts import load_contract
from agentwork.core.runner import run_contract
from agentwork.core.validation import validate_result
from agentwork.domains.sre_ops.mock_adapter import MockSREAdapter
from agentwork.storage.sqlite import get_run, init_db, save_run


class SmokeTest(unittest.TestCase):
    def test_run_and_persist_report(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        contract = load_contract(workspace / "contracts" / "sre-alerts.yaml")
        bundles = load_bundles(workspace / "bundles" / "sre-alerts.yaml")
        report = run_contract(
            contract,
            bundles,
            MockSREAdapter(),
            {"phase": "design", "trials": 3, "expectation_ids": None},
        )
        self.assertEqual(report["contract_id"], "sre-design-loop")
        self.assertEqual(report["agent_id"], "mock-sre-agent")
        self.assertIn("completion_rate", report["score"])

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "agentwork.db"
            init_db(db_path)
            save_run(report, db_path)
            loaded = get_run(report["id"], db_path)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded["id"], report["id"])

    def test_result_validation_requires_steps(self) -> None:
        with self.assertRaises(ValueError):
            validate_result(
                {
                    "response": "ok",
                    "structured": {},
                    "tool_calls": [],
                    "usage": {},
                    "latency_ms": 1,
                    "metadata": {},
                }
            )


if __name__ == "__main__":
    unittest.main()
