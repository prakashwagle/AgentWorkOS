from __future__ import annotations

import copy
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from agentwork.core.checks import evaluate_expectation_checks, evaluate_invariants
from agentwork.core.scoring import summarize_trials
from agentwork.core.validation import validate_result


def _bundle_lookup(bundles: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for bundle in bundles:
        grouped[bundle["bundle_type"]].append(bundle)
    return grouped


def run_contract(
    contract: dict[str, Any],
    bundles: list[dict[str, Any]],
    adapter: Any,
    config: dict[str, Any],
) -> dict[str, Any]:
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    by_type = _bundle_lookup(bundles)
    selected = config.get("expectation_ids")
    trial_records: list[dict[str, Any]] = []
    expectation_results: list[dict[str, Any]] = []

    for expectation in contract["expectations"]:
        if selected and expectation["id"] not in selected:
            continue
        matching_bundles = by_type.get(expectation["bundle_type"], [])
        expectation_trials: list[dict[str, Any]] = []
        for bundle in matching_bundles:
            for trial_index in range(config["trials"]):
                trial_bundle = copy.deepcopy(bundle)
                trial_bundle.setdefault("metadata", {})
                trial_bundle["metadata"]["trial_index"] = trial_index
                result = adapter.run(trial_bundle)
                validate_result(result)
                invariant_results = evaluate_invariants(contract.get("invariants", []), result)
                check_results = evaluate_expectation_checks(expectation["checks"], trial_bundle, result)
                invariant_passed = all(item["passed"] for item in invariant_results)
                deterministic_passed = all(item["passed"] for item in check_results)
                passed = invariant_passed and deterministic_passed
                notes = [item["detail"] for item in invariant_results + check_results if not item["passed"]]
                usage = result.get("usage", {})
                trial_record = {
                    "bundle_id": trial_bundle["id"],
                    "expectation_id": expectation["id"],
                    "trial_index": trial_index,
                    "passed": passed,
                    "deterministic_passed": deterministic_passed,
                    "invariant_passed": invariant_passed,
                    "latency_ms": result.get("latency_ms", 0),
                    "cost_usd": usage.get("cost_usd", 0.0),
                    "token_usage": usage,
                    "result": result,
                    "check_results": check_results,
                    "invariant_results": invariant_results,
                    "notes": notes,
                }
                expectation_trials.append(trial_record)
                trial_records.append(trial_record)

        expectation_results.append(
            {
                "expectation_id": expectation["id"],
                "description": expectation["description"],
                "trial_count": len(expectation_trials),
                "passed_trials": sum(1 for trial in expectation_trials if trial["passed"]),
                "failed_trials": sum(1 for trial in expectation_trials if not trial["passed"]),
                "trials": expectation_trials,
            }
        )

    thresholds = contract["acceptance"][config["phase"]]
    score = summarize_trials(trial_records, thresholds)
    completed_at = datetime.now(timezone.utc).isoformat()
    return {
        "id": run_id,
        "created_at": started_at,
        "completed_at": completed_at,
        "contract_id": contract["id"],
        "contract_version": contract["version"],
        "phase": config["phase"],
        "agent_id": adapter.agent_id,
        "agent_version": adapter.agent_version,
        "config": config,
        "score": score,
        "expectation_results": expectation_results,
        "trial_count": len(trial_records),
    }
