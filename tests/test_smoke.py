from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentwork.core.bundles import load_bundles
from agentwork.core.contracts import load_contract
from agentwork.core.project import load_project_config, resolve_project_paths, scaffold_project
from agentwork.core.runner import run_contract
from agentwork.core.validation import validate_result
from agentwork.domains.sre_ops.mock_adapter import MockSREAdapter
from agentwork.storage.sqlite import get_run, init_db, save_run


class SmokeTest(unittest.TestCase):
    def test_run_and_persist_report(self) -> None:
        workspace = Path(__file__).resolve().parents[1]
        contract = load_contract(workspace / "examples" / "sre" / "contracts" / "sre-alerts.yaml")
        bundles = load_bundles(workspace / "examples" / "sre" / "bundles" / "sre-alerts.yaml")
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

    def test_project_scaffold_creates_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = scaffold_project(Path(tmpdir) / "coffee-eval", template="coffee-agent")
            config = load_project_config(project_dir)
            contract_path, bundles_path, db_path = resolve_project_paths(project_dir, config, None, None)
            self.assertTrue((project_dir / "agentwork.json").exists())
            self.assertTrue(contract_path.exists())
            self.assertTrue(bundles_path.exists())
            self.assertEqual(db_path, project_dir / ".agentwork" / "agentwork.db")

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

    def test_runner_respects_expectation_bundle_ids(self) -> None:
        contract = {
            "id": "bundle-filter",
            "version": "0.1.0",
            "domain": "test",
            "description": "test",
            "acceptance": {
                "design": {
                    "min_completion_rate": 0.0,
                    "min_safety_score": 0.0,
                    "min_trials": 1,
                    "confidence": 0.9,
                }
            },
            "expectations": [
                {
                    "id": "only-first-bundle",
                    "description": "test",
                    "bundle_type": "sample",
                    "bundle_ids": ["bundle-a"],
                    "checks": [{"type": "response_contains", "text": "ok"}],
                }
            ],
        }
        bundles = [
            {"id": "bundle-a", "bundle_type": "sample", "prompt": "p1", "context": {}, "expected": {}, "metadata": {}},
            {"id": "bundle-b", "bundle_type": "sample", "prompt": "p2", "context": {}, "expected": {}, "metadata": {}},
        ]

        class TinyAdapter:
            agent_id = "tiny"
            agent_version = "0.1.0"

            def run(self, bundle):
                return {
                    "response": f"ok {bundle['id']}",
                    "structured": {},
                    "tool_calls": [],
                    "steps": [],
                    "usage": {},
                    "latency_ms": 1,
                    "metadata": {},
                }

        report = run_contract(contract, bundles, TinyAdapter(), {"phase": "design", "trials": 1})
        trials = report["expectation_results"][0]["trials"]
        self.assertEqual(len(trials), 1)
        self.assertEqual(trials[0]["bundle_id"], "bundle-a")


if __name__ == "__main__":
    unittest.main()
