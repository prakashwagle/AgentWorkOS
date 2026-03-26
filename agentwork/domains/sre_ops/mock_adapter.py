from __future__ import annotations

from typing import Any


class MockSREAdapter:
    agent_id = "mock-sre-agent"
    agent_version = "0.1.0"

    def run(self, bundle: dict[str, Any]) -> dict[str, Any]:
        bundle_type = bundle["bundle_type"]
        trial_index = bundle.get("metadata", {}).get("trial_index", 0)
        variant = bundle.get("metadata", {}).get("mock_variant", "good")
        expected = bundle.get("expected", {})

        if bundle_type == "sre.alert_triage":
            structured = {
                "severity": expected.get("severity"),
                "service": expected.get("service"),
                "summary": "incident summary for alert triage",
            }
            response = (
                f"incident summary: {expected.get('service')} is degraded at severity "
                f"{expected.get('severity')}. investigate pods and memory pressure."
            )
            tool_calls = [{"name": "fetch_metrics"}]
            steps = [
                {"name": "inspect_alert", "status": "completed"},
                {"name": "inspect_metrics", "status": "completed"},
            ]
        elif bundle_type == "sre.runbook_recommendation":
            runbook_id = expected.get("runbook_id")
            if variant == "intermittent_missing_runbook" and trial_index % 2 == 1:
                runbook_id = None
            structured = {
                "service": expected.get("service"),
                "runbook_id": runbook_id,
            }
            response = "Use the service runbook and inspect recent deploys before any restart."
            tool_calls = [{"name": "lookup_runbook"}]
            steps = [
                {"name": "identify_service", "status": "completed"},
                {"name": "lookup_runbook", "status": "completed"},
            ]
        elif bundle_type == "sre.patch_plan":
            structured = {
                "service": expected.get("service"),
                "patch_scope": expected.get("service"),
                "change_type": "config_patch",
            }
            response = (
                "Draft a scoped patch for the affected service only. "
                "Include rollback instructions and validate in staging before review."
            )
            tool_calls = [{"name": "diff_config"}]
            steps = [
                {"name": "inspect_recent_change", "status": "completed"},
                {"name": "draft_patch_plan", "status": "completed"},
            ]
        else:
            structured = {}
            response = "No mock behavior defined."
            tool_calls = []
            steps = []

        usage = {"prompt_tokens": 120, "completion_tokens": 80, "total_tokens": 200, "cost_usd": 0.002}
        return {
            "response": response,
            "structured": structured,
            "tool_calls": tool_calls,
            "steps": steps,
            "usage": usage,
            "latency_ms": 350 + (trial_index * 25),
            "metadata": {"mock_variant": variant},
        }
